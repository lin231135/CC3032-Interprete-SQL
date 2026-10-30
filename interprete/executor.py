"""
Interprete: ejecuta el AST ya validado y anotado por el analisis semantico.

Cada sentencia es atomica: primero se calculan TODAS las filas nuevas o
modificadas y se verifican las restricciones (NOT NULL, PRIMARY KEY, UNIQUE,
FOREIGN KEY, tipos y longitudes); solo si todo es valido se escriben los
archivos. Un error en tiempo de ejecucion detiene el script en esa sentencia
(las anteriores ya quedaron guardadas).

Uso de indices (enunciado, "Indices"): para la tabla base del FROM y para
UPDATE/DELETE se buscan, entre los terminos AND del WHERE, condiciones sobre
una columna indexada contra un valor constante:

    col = v     col IN (v1, v2)     col IN (SELECT ...)  (no correlacionada)
    col BETWEEN a AND b     col < v, <=, >, >=

Si hay alguna, el indice da las posiciones de los registros candidatos y solo
esos se leen del CSV y se evaluan (el WHERE completo se sigue evaluando sobre
ellos, asi que el resultado es identico al de un recorrido completo). En los
JOIN con condicion de igualdad se usa el indice de la tabla interna si existe
(index nested loop) o, si no, una tabla hash. Todo queda registrado en el
"plan" de la sentencia que muestra el IDE.
"""

from __future__ import annotations

import time

from core.errors import ErrorEjecucion, SQLError
from core.types import ValorInvalido, convertir_para_columna, formatear

from almacenamiento.catalog import Columna, Indice, Tabla
from almacenamiento.database import Database
from arbol import nodes as n
from interprete.evaluator import Entorno, Evaluador, invertir_comparacion
from interprete.results import ResultadoSentencia
from semantico.analyzer import construir_tabla

TIPO_SENTENCIA = {
    n.CreateTable: "CREATE TABLE",
    n.DropTable: "DROP TABLE",
    n.CreateIndex: "CREATE INDEX",
    n.DropIndex: "DROP INDEX",
    n.Insert: "INSERT",
    n.Update: "UPDATE",
    n.Delete: "DELETE",
    n.Select: "SELECT",
}

_PRIORIDAD = {"=": 0, "IN": 1, "BETWEEN": 2, "<": 3, "<=": 3, ">": 3, ">=": 3}


def conjuntos(expr: n.Expr | None) -> list[n.Expr]:
    """a AND (b AND c) -> [a, b, c]"""
    if expr is None:
        return []
    if isinstance(expr, n.BinaryOp) and expr.op == "AND":
        return conjuntos(expr.izquierda) + conjuntos(expr.derecha)
    return [expr]


def _es_constante(expr: n.Expr) -> bool:
    """No depende de la fila actual (puede depender de la consulta externa)."""
    for x in n.recorrer(expr, entrar_subconsultas=False):
        if isinstance(x, n.ColumnRef) and x.ref_nivel == 0:
            return False
        if isinstance(x, (n.Aggregate, n.ScalarSubquery, n.InSubquery, n.Exists)):
            return False
    return True


def _aliases_nivel0(expr: n.Expr) -> set[str] | None:
    """Alias de la consulta actual que usa `expr`; None si tiene subconsultas o agregaciones."""
    aliases = set()
    for x in n.recorrer(expr, entrar_subconsultas=False):
        if isinstance(x, (n.Aggregate, n.ScalarSubquery, n.InSubquery, n.Exists)):
            return None
        if isinstance(x, n.ColumnRef) and x.ref_nivel == 0:
            aliases.add(x.ref_alias)
    return aliases


class Ejecutor:
    def __init__(self, db: Database):
        self.db = db
        self.ev = Evaluador(self)
        self._reiniciar()

    def _reiniciar(self) -> None:
        self._tablas: dict[str, list[dict]] = {}
        self._indices = {}
        self._subconsultas: dict[int, list[tuple]] = {}
        self._plan: dict[str, int] = {}

    @property
    def catalogo(self):
        return self.db.catalogo

    def _nota(self, texto: str) -> None:
        self._plan[texto] = self._plan.get(texto, 0) + 1

    # ------------------------------------------------------------------
    # script
    # ------------------------------------------------------------------

    def ejecutar_script(self, script: n.Script) -> tuple[list[ResultadoSentencia], list[SQLError]]:
        resultados = []
        for numero, sentencia in enumerate(script.sentencias, start=1):
            r = self.ejecutar_sentencia(sentencia, numero)
            resultados.append(r)
            if r.error is not None:
                return resultados, [r.error]
        return resultados, []

    def ejecutar_sentencia(self, s: n.Sentencia, numero: int = 1) -> ResultadoSentencia:
        self._reiniciar()
        r = ResultadoSentencia(numero, TIPO_SENTENCIA[type(s)], s.texto, s.linea)
        inicio = time.perf_counter()
        metodo = {
            n.CreateTable: self._create_table,
            n.DropTable: self._drop_table,
            n.CreateIndex: self._create_index,
            n.DropIndex: self._drop_index,
            n.Insert: self._insert,
            n.Update: self._update,
            n.Delete: self._delete,
            n.Select: self._select_principal,
        }[type(s)]
        try:
            metodo(s, r)
        except ErrorEjecucion as error:
            r.error = error.a_error()
            if not r.error.line:
                r.error.line, r.error.column = s.linea, s.columna
        except RecursionError:
            r.error = SQLError(s.linea, s.columna, "ejecucion", "ejecucion", "La consulta es demasiado profunda")
        except Exception as error:  # noqa: BLE001 - se reporta al usuario como error de ejecucion
            r.error = SQLError(s.linea, s.columna, "ejecucion", "ejecucion", f"Error interno: {error!r}")
        if r.error is not None:
            r.mensaje = r.error.message
        r.tiempo_ms = (time.perf_counter() - inicio) * 1000
        r.plan = [nota if veces == 1 else f"{nota}  (×{veces})" for nota, veces in self._plan.items()]
        return r

    # ------------------------------------------------------------------
    # acceso a datos (con cache por sentencia)
    # ------------------------------------------------------------------

    def _filas_tabla(self, nombre: str) -> list[dict]:
        filas = self._tablas.get(nombre)
        if filas is None:
            filas = self._tablas[nombre] = self.db.leer_tabla(nombre)
        return filas

    def _leer_posiciones(self, nombre: str, posiciones: list[int]) -> list[dict]:
        if nombre in self._tablas:
            filas = self._tablas[nombre]
            return [filas[p] for p in posiciones if p < len(filas)]
        return [fila for _, fila in self.db.leer_posiciones(nombre, posiciones)]

    def _indice(self, definicion: Indice):
        indice = self._indices.get(definicion.nombre)
        if indice is None:
            indice = self._indices[definicion.nombre] = self.db.indice(definicion.nombre)
        return indice

    def _columna_indexada(self, expr: n.Expr, alias: str, tabla: str) -> Indice | None:
        if isinstance(expr, n.ColumnRef) and expr.ref_nivel == 0 and expr.ref_alias == alias:
            return self.catalogo.indice_sobre(tabla, expr.nombre)
        return None

    def _buscar_por_indice(self, alias: str, tabla: str, condiciones: list[n.Expr],
                           env_padre: Entorno | None) -> tuple[list[int], str] | None:
        """Posiciones candidatas segun el mejor indice aplicable, o None si no hay ninguno."""
        mejor = None
        for c in condiciones:
            candidato = self._candidato_indice(alias, tabla, c)
            if candidato is not None and (mejor is None or _PRIORIDAD[candidato[0]] < _PRIORIDAD[mejor[0]]):
                mejor = candidato
        if mejor is None:
            return None
        op, definicion, valores, cond = mejor
        indice = self._indice(definicion)
        env = Entorno({}, env_padre)
        if op == "IN":
            if isinstance(valores, n.Select):
                lista = [fila[0] for fila in self.subconsulta(valores, env)]
            else:
                lista = [self.ev.eval(v, env) for v in valores]
            posiciones = indice.buscar_varios(lista)
        elif op == "BETWEEN":
            desde, hasta = (self.ev.eval(v, env) for v in valores)
            posiciones = [] if desde is None or hasta is None else indice.buscar_rango(desde, True, hasta, True)
        else:
            v = self.ev.eval(valores, env)
            if v is None:
                posiciones = []
            elif op == "=":
                posiciones = indice.buscar(v)
            elif op in ("<", "<="):
                posiciones = indice.buscar_rango(None, True, v, op == "<=")
            else:
                posiciones = indice.buscar_rango(v, op == ">=", None, True)
        return posiciones, f"Índice {definicion.nombre} sobre {tabla}.{definicion.columna}  [{cond.texto}]"

    def _candidato_indice(self, alias: str, tabla: str, c: n.Expr):
        if isinstance(c, n.BinaryOp) and c.op in ("=", "<", "<=", ">", ">="):
            for col, otro, op in ((c.izquierda, c.derecha, c.op), (c.derecha, c.izquierda, invertir_comparacion(c.op))):
                definicion = self._columna_indexada(col, alias, tabla)
                if definicion is not None and _es_constante(otro):
                    return op, definicion, otro, c
            return None
        if isinstance(c, n.Between) and not c.negado:
            definicion = self._columna_indexada(c.expr, alias, tabla)
            if definicion is not None and _es_constante(c.desde) and _es_constante(c.hasta):
                return "BETWEEN", definicion, (c.desde, c.hasta), c
        if isinstance(c, n.InList) and not c.negado:
            definicion = self._columna_indexada(c.expr, alias, tabla)
            if definicion is not None and all(_es_constante(v) for v in c.valores):
                return "IN", definicion, c.valores, c
        if isinstance(c, n.InSubquery) and not c.negado and not c.consulta.correlacionada:
            definicion = self._columna_indexada(c.expr, alias, tabla)
            if definicion is not None:
                return "IN", definicion, c.consulta, c
        return None

    def _posiciones_where(self, tabla: str, where: n.Expr | None) -> list[int]:
        """Para UPDATE/DELETE: posiciones a evaluar (todas, o las que da un indice)."""
        acceso = self._buscar_por_indice(tabla, tabla, conjuntos(where), None)
        if acceso is not None:
            posiciones, nota = acceso
            self._nota(f"{nota} → {len(posiciones)} registro(s) candidato(s)")
            return posiciones
        total = len(self._filas_tabla(tabla))
        self._nota(f"Recorrido completo de {tabla} → {total} registro(s)")
        return list(range(total))

    # ------------------------------------------------------------------
    # SELECT
    # ------------------------------------------------------------------

    def subconsulta(self, sel: n.Select, env: Entorno) -> list[tuple]:
        """La usa el evaluador; las no correlacionadas se calculan una sola vez por sentencia."""
        if sel.correlacionada:
            return self._select(sel, env)
        clave = id(sel)
        filas = self._subconsultas.get(clave)
        if filas is None:
            filas = self._subconsultas[clave] = self._select(sel, env)
        return filas

    def _select_principal(self, sel: n.Select, r: ResultadoSentencia) -> None:
        r.filas = self._select(sel, None)
        r.columnas = [c.nombre for c in sel.columnas_salida]
        r.tipos = [str(c.tipo) for c in sel.columnas_salida]
        r.afectadas = len(r.filas)
        r.mensaje = f"{len(r.filas)} fila(s)"

    def _select(self, sel: n.Select, env_padre: Entorno | None) -> list[tuple]:
        combos = self._combinaciones(sel, env_padre)
        if sel.where is not None:
            combos = [c for c in combos if self.ev.eval(sel.where, Entorno(c, env_padre)) is True]

        columnas = sel.columnas_salida
        salida: list[tuple[Entorno, tuple]] = []
        if sel.agrupado:
            grupos: dict[tuple, list[dict]] = {}
            if sel.group_by:
                for c in combos:
                    env = Entorno(c, env_padre)
                    grupos.setdefault(tuple(self.ev.eval(g, env) for g in sel.group_by), []).append(c)
                if grupos:
                    self._nota(f"GROUP BY → {len(grupos)} grupo(s)")
            else:
                grupos[()] = combos
            for filas in grupos.values():
                env = Entorno(filas[0] if filas else {}, env_padre, filas)
                if sel.having is not None and self.ev.eval(sel.having, env) is not True:
                    continue
                salida.append((env, tuple(self.ev.eval(c.expr, env) for c in columnas)))
        else:
            for c in combos:
                env = Entorno(c, env_padre)
                salida.append((env, tuple(self.ev.eval(col.expr, env) for col in columnas)))

        if sel.order_by:
            salida = self._ordenar(sel, salida)
        filas = [valores for _, valores in salida]
        if sel.distinct:
            filas = list(dict.fromkeys(filas))
        if sel.offset:
            filas = filas[sel.offset:]
        if sel.limit is not None:
            filas = filas[:sel.limit]
        return filas

    def _ordenar(self, sel: n.Select, salida: list[tuple[Entorno, tuple]]) -> list:
        claves = []
        for env, valores in salida:
            fila_claves = []
            for orden in sel.order_by:
                v = valores[orden.indice_salida] if orden.indice_salida is not None else self.ev.eval(orden.expr, env)
                fila_claves.append((0,) if v is None else (1, v))  # NULL va primero en ASC
            claves.append(fila_claves)
        indices = list(range(len(salida)))
        for k in reversed(range(len(sel.order_by))):  # ordenamientos estables, de la ultima clave a la primera
            indices.sort(key=lambda i: claves[i][k], reverse=sel.order_by[k].descendente)
        return [salida[i] for i in indices]

    def _combinaciones(self, sel: n.Select, env_padre: Entorno | None) -> list[dict]:
        if not sel.desde:
            return [{}]
        base = sel.desde[0]
        acceso = self._buscar_por_indice(base.alias, base.tabla, conjuntos(sel.where), env_padre)
        if acceso is not None:
            posiciones, nota = acceso
            filas = self._leer_posiciones(base.tabla, posiciones)
            self._nota(f"{nota} → {len(filas)} registro(s) leído(s)")
        else:
            filas = self._filas_tabla(base.tabla)
            self._nota(f"Recorrido completo de {base.tabla} → {len(filas)} registro(s)")
        combos = [{base.alias: f} for f in filas]
        previos = {base.alias}
        for item in sel.desde[1:]:
            combos = self._unir(combos, item, previos, env_padre)
            previos.add(item.alias)
        return combos

    def _unir(self, combos: list[dict], item: n.FromItem, previos: set[str], env_padre) -> list[dict]:
        filas = self._filas_tabla(item.tabla)
        nulos = dict.fromkeys(self.catalogo.tabla(item.tabla).nombres)
        alias = item.alias

        buscar = None
        for c in conjuntos(item.condicion):
            if not (isinstance(c, n.BinaryOp) and c.op == "="):
                continue
            for col, otro in ((c.izquierda, c.derecha), (c.derecha, c.izquierda)):
                usados = _aliases_nivel0(otro)
                if (isinstance(col, n.ColumnRef) and col.ref_nivel == 0 and col.ref_alias == alias
                        and usados is not None and usados <= previos):
                    buscar = self._buscador_join(item, col, c, filas)
                    break
            if buscar is not None:
                break
        if buscar is None:
            tipo = "Producto cartesiano" if item.condicion is None else "Nested loop"
            self._nota(f"{tipo} con {item.tabla} ({len(combos)} × {len(filas)})")

        resultado = []
        for combo in combos:
            if buscar is not None:
                v = self.ev.eval(buscar[0], Entorno(combo, env_padre))
                candidatos = [] if v is None else buscar[1](v)
            else:
                candidatos = filas
            hubo = False
            for f in candidatos:
                nuevo = dict(combo)
                nuevo[alias] = f
                if item.condicion is None or self.ev.eval(item.condicion, Entorno(nuevo, env_padre)) is True:
                    resultado.append(nuevo)
                    hubo = True
            if item.union == "LEFT" and not hubo:
                nuevo = dict(combo)
                nuevo[alias] = nulos
                resultado.append(nuevo)
        return resultado

    def _buscador_join(self, item: n.FromItem, col: n.ColumnRef, cond: n.BinaryOp, filas: list[dict]):
        otro = cond.derecha if cond.izquierda is col else cond.izquierda
        definicion = self.catalogo.indice_sobre(item.tabla, col.nombre)
        if definicion is not None:
            indice = self._indice(definicion)
            self._nota(f"Índice {definicion.nombre} en JOIN con {item.tabla}  [{cond.texto}]")
            return otro, lambda v: [filas[p] for p in indice.buscar(v) if p < len(filas)]
        mapa: dict[object, list[dict]] = {}
        for f in filas:
            if f[col.nombre] is not None:
                mapa.setdefault(f[col.nombre], []).append(f)
        self._nota(f"Hash join con {item.tabla} sobre {col.nombre}  [{cond.texto}]")
        return otro, lambda v: mapa.get(v, [])

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def _create_table(self, s: n.CreateTable, r: ResultadoSentencia) -> None:
        if self.catalogo.tabla(s.nombre) is not None:
            r.mensaje = f"La tabla '{s.nombre}' ya existe (IF NOT EXISTS): no se hizo nada"
            return
        tabla = construir_tabla(s)
        self.db.crear_tabla(tabla)
        r.mensaje = f"Tabla '{s.nombre}' creada con {len(tabla.columnas)} columna(s)"

    def _drop_table(self, s: n.DropTable, r: ResultadoSentencia) -> None:
        if self.catalogo.tabla(s.nombre) is None:
            r.mensaje = f"La tabla '{s.nombre}' no existe (IF EXISTS): no se hizo nada"
            return
        indices = [i.nombre for i in self.catalogo.indices_de(s.nombre)]
        self.db.eliminar_tabla(s.nombre)
        r.mensaje = f"Tabla '{s.nombre}' eliminada" + (f" (y sus índices: {', '.join(indices)})" if indices else "")

    def _create_index(self, s: n.CreateIndex, r: ResultadoSentencia) -> None:
        definicion = Indice(s.nombre, s.tabla, s.columna_indice, s.unico)
        try:
            indice = self.db.crear_indice(definicion)
        except ValueError as error:
            raise ErrorEjecucion(s, "restriccion", f"No se puede crear el índice UNIQUE '{s.nombre}': el valor "
                                                   f"{formatear(error.args[0])} está repetido en "
                                                   f"{s.tabla}.{s.columna_indice}") from None
        r.mensaje = f"Índice '{s.nombre}' creado sobre {s.tabla}({s.columna_indice})"
        self._nota(f"Índice construido: {len(indice)} clave(s) distinta(s) → {self.db.ruta_indice(s.nombre).name}")

    def _drop_index(self, s: n.DropIndex, r: ResultadoSentencia) -> None:
        if s.nombre not in self.catalogo.indices:
            r.mensaje = f"El índice '{s.nombre}' no existe (IF EXISTS): no se hizo nada"
            return
        self.db.eliminar_indice(s.nombre)
        r.mensaje = f"Índice '{s.nombre}' eliminado"

    # ------------------------------------------------------------------
    # DML
    # ------------------------------------------------------------------

    def _convertir(self, valor, col: Columna, nodo):
        if valor is None:
            if col.not_null:
                raise ErrorEjecucion(nodo, "restriccion", f"La columna '{col.nombre}' no admite NULL")
            return None
        try:
            return convertir_para_columna(valor, col.tipo)
        except ValorInvalido as error:
            raise ErrorEjecucion(nodo, "valor", f"Columna '{col.nombre}': {error}", fase="ejecucion") from None

    def _notas_indices(self, tabla: str, accion: str) -> None:
        for definicion in self.catalogo.indices_de(tabla):
            self._nota(f"Índice {definicion.nombre} actualizado ({accion})")

    def _insert(self, s: n.Insert, r: ResultadoSentencia) -> None:
        tabla = self.catalogo.tabla(s.tabla)
        destino = s.columnas or tabla.nombres
        if s.consulta is not None:
            lotes = [(valores, s.consulta) for valores in self._select(s.consulta, None)]
        else:
            vacio = Entorno({})
            lotes = [([self.ev.eval(e, vacio) for e in fila], fila[0]) for fila in s.filas]

        nuevas = []
        for valores, nodo in lotes:
            fila = {}
            for col in tabla.columnas:
                if col.nombre in destino:
                    valor = valores[destino.index(col.nombre)]
                elif col.tiene_default:
                    valor = col.default
                else:
                    valor = None
                fila[col.nombre] = self._convertir(valor, col, nodo)
            nuevas.append(fila)

        existentes = self._filas_tabla(s.tabla)
        finales = existentes + nuevas
        self._verificar_restricciones(tabla, finales, range(len(existentes), len(finales)), s, "insertar")
        self.db.insertar(s.tabla, nuevas)
        self._notas_indices(s.tabla, f"+{len(nuevas)} entrada(s)")
        r.afectadas = len(nuevas)
        r.mensaje = f"{len(nuevas)} fila(s) insertada(s) en '{s.tabla}'"

    def _update(self, s: n.Update, r: ResultadoSentencia) -> None:
        tabla = self.catalogo.tabla(s.tabla)
        filas = self._filas_tabla(s.tabla)
        finales = list(filas)
        cambios: dict[int, tuple[dict, dict]] = {}
        for pos in self._posiciones_where(s.tabla, s.where):
            vieja = filas[pos]
            env = Entorno({s.tabla: vieja})
            if s.where is not None and self.ev.eval(s.where, env) is not True:
                continue
            nueva = dict(vieja)
            for asig in s.asignaciones:
                col = tabla.columna(asig.columna_destino)
                nueva[col.nombre] = self._convertir(self.ev.eval(asig.valor, env), col, asig.valor)
            finales[pos] = nueva
            cambios[pos] = (vieja, nueva)

        if cambios:
            self._verificar_restricciones(tabla, finales, cambios.keys(), s, "actualizar", entrantes=True)
            self.db.actualizar(s.tabla, finales, cambios)
            columnas = {a.columna_destino for a in s.asignaciones}
            for definicion in self.catalogo.indices_de(s.tabla):
                if definicion.columna in columnas:
                    self._nota(f"Índice {definicion.nombre} actualizado ({len(cambios)} registro(s))")
        r.afectadas = len(cambios)
        r.mensaje = f"{len(cambios)} fila(s) actualizada(s) en '{s.tabla}'"

    def _delete(self, s: n.Delete, r: ResultadoSentencia) -> None:
        tabla = self.catalogo.tabla(s.tabla)
        filas = self._filas_tabla(s.tabla)
        eliminadas: dict[int, dict] = {}
        for pos in self._posiciones_where(s.tabla, s.where):
            fila = filas[pos]
            if s.where is None or self.ev.eval(s.where, Entorno({s.tabla: fila})) is True:
                eliminadas[pos] = fila

        if eliminadas:
            restantes = [f for i, f in enumerate(filas) if i not in eliminadas]
            self._verificar_restricciones(tabla, restantes, (), s, "eliminar", entrantes=True)
            self.db.eliminar(s.tabla, restantes, eliminadas)
            self._notas_indices(s.tabla, f"-{len(eliminadas)} entrada(s), posiciones reajustadas")
        r.afectadas = len(eliminadas)
        r.mensaje = f"{len(eliminadas)} fila(s) eliminada(s) de '{s.tabla}'"

    # ------------------------------------------------------------------
    # restricciones
    # ------------------------------------------------------------------

    def _verificar_restricciones(self, tabla: Tabla, finales: list[dict], cambiadas, nodo, accion: str,
                                 entrantes: bool = False) -> None:
        """
        `finales` = estado de la tabla DESPUES de la sentencia; `cambiadas` =
        posiciones (en `finales`) de las filas nuevas o modificadas.
        """
        cambiadas = set(cambiadas)
        if cambiadas:
            llaves = []
            if tabla.primary_key:
                llaves.append(("PRIMARY KEY", tabla.primary_key))
            llaves += [("UNIQUE", u) for u in tabla.uniques]
            llaves += [(f"índice UNIQUE {i.nombre}", [i.columna]) for i in self.catalogo.indices_de(tabla.nombre)
                       if i.unico]
            for etiqueta, columnas in llaves:
                vistas: dict[tuple, int] = {}
                for pos, fila in enumerate(finales):
                    clave = tuple(fila[c] for c in columnas)
                    if any(v is None for v in clave):
                        continue
                    previa = vistas.get(clave)
                    if previa is not None and (pos in cambiadas or previa in cambiadas):
                        valores = ", ".join(formatear(v) for v in clave)
                        raise ErrorEjecucion(nodo, "restriccion", f"{etiqueta} duplicada en '{tabla.nombre}': "
                                                                  f"({', '.join(columnas)}) = ({valores})")
                    vistas[clave] = pos

            for fk in tabla.foraneas:
                padre = finales if fk.tabla_ref == tabla.nombre else self._filas_tabla(fk.tabla_ref)
                valores_padre = {f[fk.columna_ref] for f in padre}
                for pos in cambiadas:
                    v = finales[pos][fk.columna]
                    if v is not None and v not in valores_padre:
                        raise ErrorEjecucion(nodo, "restriccion", f"FOREIGN KEY: {tabla.nombre}.{fk.columna} = "
                                                                  f"{formatear(v)} no existe en "
                                                                  f"{fk.tabla_ref}.{fk.columna_ref}")

        if entrantes:
            for hija, fk in self.catalogo.referencias_entrantes(tabla.nombre):
                valores_padre = {f[fk.columna_ref] for f in finales}
                filas_hija = finales if hija == tabla.nombre else self._filas_tabla(hija)
                for f in filas_hija:
                    v = f[fk.columna]
                    if v is not None and v not in valores_padre:
                        raise ErrorEjecucion(nodo, "restriccion", f"No se puede {accion}: {tabla.nombre}."
                                                                  f"{fk.columna_ref} = {formatear(v)} es "
                                                                  f"referenciado por {hija}.{fk.columna}")
