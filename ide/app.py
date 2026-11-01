"""
IDE del Interprete SQL (CustomTkinter + Tk) con estilo oscuro tipo Visual Studio Code.

Escribir/abrir un .sql, analizarlo y ejecutarlo sobre la base de datos (una
carpeta con metadata.txt, los .csv y los indices) y ver los resultados, los
mensajes y el plan de acceso, los problemas (lexicos, sintacticos, semanticos
y de ejecucion), los tokens, el arbol sintactico, el AST y la bateria de
pruebas. Los paneles se alimentan de `driver.Resultado`; el interprete NO se
reimplementa aqui.

Atajos: F5 (o Ctrl+Enter) ejecutar, F6 solo analizar, F7 correr la bateria,
Ctrl+S guardar, Ctrl+O abrir, Ctrl+/ comentar, Ctrl+rueda o Ctrl +/- para el
zoom. Si hay texto seleccionado, F5/F6 trabajan solo sobre la seleccion.
"""

from __future__ import annotations

import bisect
import io
import pathlib
import re
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image, ImageTk

from almacenamiento.database import Database
from arbol.render import ast_png, ast_texto, dot_disponible, parse_tree_png, parse_tree_texto
from core.errors import NOMBRE_FASE
from driver import BD_POR_DEFECTO, Resultado, analizar
from pruebas.runner import ejecutar_bateria

ctk.set_appearance_mode("dark")

MAX_NODOS_ARBOL = 500
MAX_FILAS_GRILLA = 1000
ZOOM_PASO = 1.25
RAIZ_PRUEBAS = pathlib.Path(__file__).resolve().parent.parent / "pruebas"

# --- Paleta (Dark+) -----------------------------------------------------
BG = "#1e1e1e"
BG_LATERAL = "#252526"
BG_BARRA = "#333333"
BG_TAB = "#2d2d2d"
BG_FILA_ALT = "#232324"
BORDE = "#3c3c3c"
TEXTO = "#d4d4d4"
TEXTO_TENUE = "#858585"
SELECCION = "#264f78"
LINEA_ACTUAL = "#2a2d2e"
LINEA_ERROR = "#4b1818"
AZUL = "#007acc"
ROJO = "#c5392b"
VERDE = "#2ea043"

COLORES_SINTAXIS = {
    "kw_ctrl": "#c586c0",
    "kw": "#569cd6",
    "tipo": "#4ec9b0",
    "const": "#569cd6",
    "tabla": "#4ec9b0",
    "columna": "#9cdcfe",
    "funcion": "#dcdcaa",
    "numero": "#b5cea8",
    "cadena": "#ce9178",
    "comentario": "#6a9955",
}

SENTENCIAS = {"SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP"}
KW = {"DISTINCT", "FROM", "WHERE", "GROUP", "BY", "HAVING", "ORDER", "ASC", "DESC", "LIMIT", "OFFSET", "AS",
      "JOIN", "INNER", "LEFT", "OUTER", "CROSS", "ON", "AND", "OR", "NOT", "IN", "EXISTS", "BETWEEN", "LIKE", "IS",
      "INTO", "VALUES", "SET", "TABLE", "INDEX", "UNIQUE", "PRIMARY", "KEY", "FOREIGN", "REFERENCES", "DEFAULT",
      "IF"}
TIPOS = {"INT", "INTEGER", "FLOAT", "VARCHAR", "BOOLEAN", "DATE"}
CONSTANTES = {"TRUE", "FALSE", "NULL"}
FUNCIONES = {"COUNT", "SUM", "AVG", "MIN", "MAX"}

RE_FUENTE = re.compile(
    r"(?P<comentario>--[^\n]*|/\*.*?(?:\*/|$))"
    r"|(?P<cadena>'(?:[^'\n]|'')*'?)"
    r"|(?P<numero>\b\d+(?:\.\d*)?\b|\.\d+\b)"
    r"|(?P<palabra>[A-Za-z_À-ÿ][\wÀ-ÿ]*)",
    re.S,
)

EJEMPLO = '''-- Intérprete SQL: escriba aquí y presione F5 para ejecutar (F6 solo analiza).
-- Con texto seleccionado, F5 ejecuta solo la selección.

CREATE TABLE IF NOT EXISTS estudiantes (
    id      INT PRIMARY KEY,
    nombre  VARCHAR(50) NOT NULL,
    edad    INT,
    activo  BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS cursos (
    id        INT PRIMARY KEY,
    nombre    VARCHAR(40) NOT NULL,
    creditos  INT
);

CREATE TABLE IF NOT EXISTS inscripciones (
    estudiante_id  INT REFERENCES estudiantes(id),
    curso_id       INT REFERENCES cursos(id),
    PRIMARY KEY (estudiante_id, curso_id)
);

-- (ejecute los INSERT una sola vez: la PRIMARY KEY no admite repetidos)
INSERT INTO estudiantes (id, nombre, edad) VALUES
    (1, 'Ana', 20), (2, 'Bruno', 17), (3, 'Carla', 22), (4, 'Diego', 19);
INSERT INTO cursos VALUES (1, 'Compiladores', 5), (2, 'Bases de Datos', 4), (3, 'Cálculo', 3);
INSERT INTO inscripciones VALUES (1, 1), (1, 3), (2, 3), (3, 2), (4, 3);

CREATE INDEX idx_edad ON estudiantes (edad);

SELECT nombre
FROM estudiantes
WHERE edad >= 18;

SELECT nombre
FROM estudiantes
WHERE id IN (SELECT estudiante_id
             FROM inscripciones
             WHERE curso_id = 3);

SELECT c.nombre, COUNT(*) AS inscritos
FROM cursos c INNER JOIN inscripciones i ON i.curso_id = c.id
GROUP BY c.nombre
HAVING COUNT(*) >= 1
ORDER BY inscritos DESC;
'''


class VisorImagen:
    """Lienzo con zoom y desplazamiento para el arbol sintactico y el AST."""

    def __init__(self, ide: "SQLIDE", padre: tk.Frame):
        self.ide = ide
        self.pil: Image.Image | None = None
        self.tk: ImageTk.PhotoImage | None = None
        self.zoom = 1.0

        barra = tk.Frame(padre, bg=BG_LATERAL)
        barra.pack(side="top", fill="x")
        ide._boton(barra, "Acercar  +", lambda: self.zoom_paso(ZOOM_PASO), bg=BG_LATERAL).pack(side="left", pady=3)
        ide._boton(barra, "Alejar  −", lambda: self.zoom_paso(1 / ZOOM_PASO), bg=BG_LATERAL).pack(side="left", pady=3)
        ide._boton(barra, "Ajustar", self.ajustar, bg=BG_LATERAL).pack(side="left", pady=3)
        self.lbl_info = tk.Label(barra, text="", bg=BG_LATERAL, fg=TEXTO_TENUE, font=ide.f_tenue)
        self.lbl_info.pack(side="right", padx=12)

        marco = tk.Frame(padre, bg=BG)
        marco.pack(side="top", fill="both", expand=True)
        self.canvas = tk.Canvas(marco, bg="#ffffff", highlightthickness=0)
        sy = ttk.Scrollbar(marco, orient="vertical", command=self.canvas.yview)
        sx = ttk.Scrollbar(marco, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        marco.rowconfigure(0, weight=1)
        marco.columnconfigure(0, weight=1)
        self.canvas.bind("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1 if e.delta > 0 else 1, "units"))
        self.canvas.bind("<Shift-MouseWheel>", lambda e: self.canvas.xview_scroll(-1 if e.delta > 0 else 1, "units"))
        self.canvas.bind("<Control-MouseWheel>", lambda e: self.zoom_paso(ZOOM_PASO if e.delta > 0 else 1 / ZOOM_PASO))
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))

    def limpiar(self, mensaje: str = "") -> None:
        self.pil = None
        self.tk = None
        self.zoom = 1.0
        self.canvas.delete("all")
        self.lbl_info.configure(text="")
        if mensaje:
            self.canvas.create_text(16, 16, anchor="nw", text=mensaje, font=self.ide.f_ui, fill="#555555")

    def mostrar_png(self, png: bytes, info: str = "") -> None:
        self.limpiar()
        self.pil = Image.open(io.BytesIO(png))
        self.lbl_info.configure(text=info)
        ancho = self.canvas.winfo_width()
        if ancho > 100 and self.pil.width > ancho:  # que quepa a lo ancho, sin volverse ilegible
            self.zoom = max(ancho / self.pil.width, 0.6)
        self._dibujar()

    def mostrar_texto(self, texto: str, info: str = "") -> None:
        self.limpiar()
        self.lbl_info.configure(text=info)
        self.canvas.create_text(14, 14, anchor="nw", text=texto, font=self.ide.f_panel, fill="#1e1e1e")
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _dibujar(self) -> None:
        if self.pil is None:
            return
        ancho = max(int(self.pil.width * self.zoom), 1)
        alto = max(int(self.pil.height * self.zoom), 1)
        self.tk = ImageTk.PhotoImage(self.pil.resize((ancho, alto), Image.LANCZOS))
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk)
        self.canvas.configure(scrollregion=(0, 0, ancho, alto))

    def zoom_paso(self, factor: float) -> None:
        if self.pil is None:
            return
        self.zoom = max(0.1, min(4.0, self.zoom * factor))
        self._dibujar()

    def ajustar(self) -> None:
        if self.pil is None:
            return
        ancho = max(self.canvas.winfo_width(), 100)
        alto = max(self.canvas.winfo_height(), 100)
        self.zoom = min(ancho / self.pil.width, alto / self.pil.height, 1.5)
        self._dibujar()


class SQLIDE(ctk.CTk):
    def __init__(self, ruta_bd: str | pathlib.Path = BD_POR_DEFECTO) -> None:
        super().__init__()
        self.title("Intérprete SQL")
        self._centrar_ventana(1440, 900)
        self.minsize(960, 640)
        self.configure(fg_color=BG)

        self.db = Database(ruta_bd)
        self.ruta_actual: pathlib.Path | None = None
        self.modificado = False
        self.resultado: Resultado | None = None
        self.lineas_error: set[int] = set()
        self._job_resaltado: str | None = None
        self._rutas_explorador: dict[str, pathlib.Path] = {}
        self._tablas_explorador: dict[str, str] = {}
        self._arboles_pendientes: set[str] = set()
        self._resultados_por_iid: dict[str, object] = {}
        self._orden_grilla: tuple[int, bool] | None = None
        self._filas_grilla: list[tuple] = []

        self._crear_fuentes()
        self._crear_estilos()
        self._construir_barra_herramientas()
        self._construir_barra_estado()
        self._construir_cuerpo()
        self._atar_atajos()

        self.editor.insert("1.0", EJEMPLO)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self._despues_de_editar()
        self._actualizar_titulo()

    def _centrar_ventana(self, ancho: int, alto: int) -> None:
        """Tamano en pixeles reales (sin el escalado de CTk), limitado a la pantalla."""
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(ancho, int(sw * 0.94)), min(alto, int(sh * 0.86))
        tk.Tk.geometry(self, f"{w}x{h}+{(sw - w) // 2}+{max(0, (sh - h) // 2 - 24)}")

    # ------------------------------------------------------------------
    # Fuentes y estilos
    # ------------------------------------------------------------------

    def _crear_fuentes(self) -> None:
        disponibles = set(tkfont.families())
        mono = next((f for f in ("Cascadia Code", "Consolas", "Courier New") if f in disponibles), "Courier")
        ui = "Segoe UI" if "Segoe UI" in disponibles else "Helvetica"
        self.f_editor = tkfont.Font(family=mono, size=15)
        self.f_panel = tkfont.Font(family=mono, size=13)
        self.f_grilla = tkfont.Font(family=mono, size=12)
        self.f_ui = tkfont.Font(family=ui, size=12)
        self.f_ui_b = tkfont.Font(family=ui, size=12, weight="bold")
        self.f_tenue = tkfont.Font(family=ui, size=10)
        self.f_logo = tkfont.Font(family=ui, size=13, weight="bold")

    def _crear_estilos(self) -> None:
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("TFrame", background=BG)
        s.configure("Treeview", background=BG, fieldbackground=BG, foreground=TEXTO, borderwidth=0,
                    font=self.f_ui, rowheight=30, bordercolor=BG, lightcolor=BG, darkcolor=BG)
        s.map("Treeview", background=[("selected", "#094771")], foreground=[("selected", "#ffffff")])
        s.configure("Treeview.Heading", background=BG_LATERAL, foreground=TEXTO_TENUE, relief="flat",
                    font=self.f_tenue, padding=(8, 6))
        s.map("Treeview.Heading", background=[("active", BG_TAB)])

        s.configure("Lateral.Treeview", background=BG_LATERAL, fieldbackground=BG_LATERAL, rowheight=26,
                    bordercolor=BG_LATERAL, lightcolor=BG_LATERAL, darkcolor=BG_LATERAL)
        s.map("Lateral.Treeview", background=[("selected", "#37373d")])

        s.configure("Grilla.Treeview", font=self.f_grilla, rowheight=26)

        s.configure("TNotebook", background=BG_LATERAL, borderwidth=0, tabmargins=(8, 4, 0, 0),
                    bordercolor=BG, lightcolor=BG, darkcolor=BG)
        s.configure("TNotebook.Tab", background=BG_LATERAL, foreground=TEXTO_TENUE, padding=(18, 10),
                    font=self.f_tenue, borderwidth=0, bordercolor=BG_LATERAL, lightcolor=BG_LATERAL,
                    darkcolor=BG_LATERAL)
        s.map("TNotebook.Tab", background=[("selected", BG), ("active", BG_TAB)],
              foreground=[("selected", "#ffffff"), ("active", TEXTO)],
              bordercolor=[("selected", BG)], lightcolor=[("selected", AZUL), ("active", BG_TAB)],
              darkcolor=[("selected", BG)])

        for orient, nombre in (("Vertical", "Vertical.TScrollbar"), ("Horizontal", "Horizontal.TScrollbar")):
            s.layout(nombre, [(f"{orient}.Scrollbar.trough", {"children": [
                (f"{orient}.Scrollbar.thumb", {"expand": "1", "sticky": "nswe"})], "sticky": "nswe"})])
            s.configure(nombre, background="#424242", troughcolor=BG, bordercolor=BG, lightcolor="#424242",
                        darkcolor="#424242", gripcount=0, width=13)
            s.map(nombre, background=[("active", "#686868"), ("pressed", "#7a7a7a")])

    # ------------------------------------------------------------------
    # Construccion de la UI
    # ------------------------------------------------------------------

    def _boton(self, padre, texto, comando, bg=BG_BARRA, fg=TEXTO, hover="#4a4a4a", negrita=False):
        etiqueta = tk.Label(padre, text=texto, bg=bg, fg=fg, padx=14, pady=7, cursor="hand2",
                            font=self.f_ui_b if negrita else self.f_ui)
        etiqueta.bind("<Button-1>", lambda _e: comando())
        etiqueta.bind("<Enter>", lambda _e: etiqueta.configure(bg=hover))
        etiqueta.bind("<Leave>", lambda _e: etiqueta.configure(bg=bg))
        return etiqueta

    def _construir_barra_herramientas(self) -> None:
        barra = tk.Frame(self, bg=BG_BARRA, height=46)
        barra.pack(side="top", fill="x")
        barra.pack_propagate(False)

        tk.Label(barra, text="  ▦  Intérprete SQL", bg=BG_BARRA, fg="#4fc1ff", font=self.f_logo).pack(
            side="left", padx=(6, 18))

        self._boton(barra, "Abrir", self.abrir_archivo).pack(side="left", pady=5)
        self._boton(barra, "Guardar", self.guardar_archivo).pack(side="left", pady=5)
        tk.Frame(barra, bg=BORDE, width=1).pack(side="left", fill="y", pady=10, padx=10)
        self._boton(barra, "▶  Ejecutar  F5", self.ejecutar, bg=VERDE, fg="#ffffff", hover="#3fb950",
                    negrita=True).pack(side="left", pady=7)
        tk.Frame(barra, bg=BG_BARRA, width=6).pack(side="left")
        self._boton(barra, "⚙  Analizar  F6", self.analizar, bg=AZUL, fg="#ffffff",
                    hover="#1a8ad4", negrita=True).pack(side="left", pady=7)
        tk.Frame(barra, bg=BG_BARRA, width=6).pack(side="left")
        self._boton(barra, "✔  Batería  F7", self.correr_bateria).pack(side="left", pady=5)
        tk.Frame(barra, bg=BORDE, width=1).pack(side="left", fill="y", pady=10, padx=10)
        self._boton(barra, "Base de datos…", self.elegir_base).pack(side="left", pady=5)

        self._boton(barra, "A+", lambda: self._zoom_editor(1)).pack(side="right", pady=5, padx=(0, 8))
        self._boton(barra, "A-", lambda: self._zoom_editor(-1)).pack(side="right", pady=5)

    def _construir_barra_estado(self) -> None:
        self.barra_estado = tk.Frame(self, bg=AZUL, height=28)
        self.barra_estado.pack(side="bottom", fill="x")
        self.barra_estado.pack_propagate(False)

        self.lbl_estado = tk.Label(self.barra_estado, text="  Listo", bg=AZUL, fg="#ffffff", font=self.f_ui_b,
                                   anchor="w")
        self.lbl_estado.pack(side="left", fill="y", padx=(4, 0))

        self.lbl_posicion = tk.Label(self.barra_estado, text="Ln 1, Col 1", bg=AZUL, fg="#ffffff", font=self.f_ui)
        self.lbl_zoom = tk.Label(self.barra_estado, text="", bg=AZUL, fg="#ffffff", font=self.f_ui)
        self.lbl_bd = tk.Label(self.barra_estado, text="", bg=AZUL, fg="#ffffff", font=self.f_ui)
        for lbl in (tk.Label(self.barra_estado, text="SQL   ", bg=AZUL, fg="#ffffff", font=self.f_ui),
                    tk.Label(self.barra_estado, text="UTF-8   ", bg=AZUL, fg="#ffffff", font=self.f_ui),
                    self.lbl_bd, self.lbl_zoom, self.lbl_posicion):
            lbl.pack(side="right", fill="y", padx=6)
        self._actualizar_zoom_label()
        self._actualizar_bd_label()

    def _construir_cuerpo(self) -> None:
        horizontal = tk.PanedWindow(self, orient="horizontal", bg=BORDE, bd=0, sashwidth=4, sashrelief="flat")
        horizontal.pack(side="top", fill="both", expand=True)

        horizontal.add(self._construir_explorador(horizontal), minsize=210, width=290)

        vertical = tk.PanedWindow(horizontal, orient="vertical", bg=BORDE, bd=0, sashwidth=4, sashrelief="flat")
        horizontal.add(vertical, minsize=420)
        vertical.add(self._construir_editor(vertical), minsize=220, height=480)
        vertical.add(self._construir_panel(vertical), minsize=150)

    # --- explorador ------------------------------------------------------

    def _seccion_lateral(self, padre, titulo: str, subtitulo: str) -> ttk.Treeview:
        marco = tk.Frame(padre, bg=BG_LATERAL)
        tk.Label(marco, text=titulo, bg=BG_LATERAL, fg=TEXTO_TENUE, font=self.f_tenue, anchor="w",
                 padx=16, pady=10).pack(fill="x")
        tk.Label(marco, text=subtitulo, bg=BG_LATERAL, fg=TEXTO_TENUE, font=self.f_tenue, anchor="w",
                 padx=16).pack(fill="x", pady=(0, 6))
        contenedor = tk.Frame(marco, bg=BG_LATERAL)
        contenedor.pack(fill="both", expand=True)
        arbol = ttk.Treeview(contenedor, show="tree", style="Lateral.Treeview", selectmode="browse")
        barra = ttk.Scrollbar(contenedor, orient="vertical", command=arbol.yview)
        arbol.configure(yscrollcommand=barra.set)
        arbol.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")
        arbol.tag_configure("valido", foreground="#89d185")
        arbol.tag_configure("invalido", foreground="#f48771")
        arbol.tag_configure("carpeta", foreground="#cccccc")
        arbol.tag_configure("tabla", foreground="#4ec9b0")
        arbol.tag_configure("columna", foreground="#9cdcfe")
        arbol.tag_configure("indice", foreground="#dcdcaa")
        arbol.tag_configure("tenue", foreground=TEXTO_TENUE)
        padre.add(marco, minsize=120)
        return arbol

    def _construir_explorador(self, padre) -> tk.PanedWindow:
        lateral = tk.PanedWindow(padre, orient="vertical", bg=BORDE, bd=0, sashwidth=3, sashrelief="flat")

        self.arbol_bd = self._seccion_lateral(lateral, "BASE DE DATOS", "Doble clic en una tabla para ver sus datos")
        self.arbol_bd.bind("<Double-1>", self._on_ver_tabla)
        self.arbol_bd.bind("<Return>", self._on_ver_tabla)

        self.explorador = self._seccion_lateral(lateral, "SCRIPTS", "Ejemplos y pruebas (doble clic para abrir)")
        self.explorador.bind("<Double-1>", self._on_abrir_desde_explorador)
        self.explorador.bind("<Return>", self._on_abrir_desde_explorador)

        self._poblar_bd()
        self._poblar_explorador()
        return lateral

    def _poblar_bd(self) -> None:
        a = self.arbol_bd
        abiertas = {self._tablas_explorador[i] for i in a.get_children()
                    if a.item(i, "open") and i in self._tablas_explorador}
        a.delete(*a.get_children())
        self._tablas_explorador.clear()
        try:
            self.db.recargar()
        except ValueError as error:
            a.insert("", "end", text=f"  ✖ {error}", tags=("invalido",))
            return
        cat = self.db.catalogo
        if not cat.tablas:
            a.insert("", "end", text="  (sin tablas: use CREATE TABLE)", tags=("tenue",))
        for t in cat.tablas.values():
            try:
                filas = self.db.contar(t.nombre)
            except (OSError, ValueError):
                filas = "?"
            nodo = a.insert("", "end", text=f"{t.nombre}   ({filas})", tags=("tabla",), open=t.nombre in abiertas)
            self._tablas_explorador[nodo] = t.nombre
            fks = {fk.columna: fk for fk in t.foraneas}
            for c in t.columnas:
                marcas = []
                if c.nombre in t.primary_key:
                    marcas.append("PK")
                if c.nombre in fks:
                    marcas.append(f"FK→{fks[c.nombre].tabla_ref}")
                if [c.nombre] in t.uniques:
                    marcas.append("UNIQUE")
                if c.not_null and c.nombre not in t.primary_key:
                    marcas.append("NOT NULL")
                extra = f"   {' · '.join(marcas)}" if marcas else ""
                a.insert(nodo, "end", text=f"   {c.nombre}  {c.tipo}{extra}", tags=("columna",))
            for i in cat.indices_de(t.nombre):
                a.insert(nodo, "end", text=f"   ⚡ {i.nombre} ({i.columna}){' UNIQUE' if i.unico else ''}",
                         tags=("indice",))

    def _poblar_explorador(self) -> None:
        self.explorador.delete(*self.explorador.get_children())
        self._rutas_explorador.clear()
        if not RAIZ_PRUEBAS.exists():
            return
        categorias = [d for d in sorted(RAIZ_PRUEBAS.iterdir()) if d.is_dir() and not d.name.startswith("__")]
        categorias.sort(key=lambda d: (d.name != "demo", d.name))
        for cat in categorias:
            nodo_cat = self.explorador.insert("", "end", text=cat.name, tags=("carpeta",),
                                              open=(cat.name == "demo"))
            archivos = sorted(cat.glob("*.sql")) + [a for sub in sorted(cat.iterdir()) if sub.is_dir()
                                                    for a in sorted(sub.glob("*.sql"))]
            for archivo in archivos:
                es_invalido = archivo.parent.name == "invalidos"
                etiqueta = archivo.name if archivo.parent == cat else f"{archivo.parent.name[:3]}/{archivo.name}"
                iid = self.explorador.insert(nodo_cat, "end", text=f"   {etiqueta}",
                                             tags=("invalido" if es_invalido else "valido",))
                self._rutas_explorador[iid] = archivo

    def _on_abrir_desde_explorador(self, _evento=None) -> None:
        seleccion = self.explorador.selection()
        if seleccion and seleccion[0] in self._rutas_explorador:
            self.cargar_archivo(self._rutas_explorador[seleccion[0]])

    def _on_ver_tabla(self, _evento=None) -> str | None:
        seleccion = self.arbol_bd.selection()
        if not seleccion or seleccion[0] not in self._tablas_explorador:
            return None
        tabla = self._tablas_explorador[seleccion[0]]
        r = analizar(f"SELECT * FROM {tabla} LIMIT {MAX_FILAS_GRILLA};", self.db, ejecutar=True)
        if r.resultados and r.resultados[0].ok:
            self._mostrar_grilla(r.resultados[0], titulo=f"{tabla}  (vista previa, no modifica el editor)")
            self._seleccionar_pestana("resultados")
        return "break"

    # --- editor -----------------------------------------------------------

    def _construir_editor(self, padre) -> tk.Frame:
        marco = tk.Frame(padre, bg=BG)

        tabs = tk.Frame(marco, bg=BG_LATERAL, height=40)
        tabs.pack(fill="x")
        tabs.pack_propagate(False)
        self.lbl_tab = tk.Label(tabs, text="", bg=BG, fg="#ffffff", font=self.f_ui, padx=18, anchor="w")
        self.lbl_tab.pack(side="left", fill="y")

        cuerpo = tk.Frame(marco, bg=BG)
        cuerpo.pack(fill="both", expand=True)

        self.gutter = tk.Canvas(cuerpo, bg=BG, width=64, highlightthickness=0, bd=0)
        self.gutter.pack(side="left", fill="y")

        self.scroll_y = ttk.Scrollbar(cuerpo, orient="vertical")
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x = ttk.Scrollbar(marco, orient="horizontal")
        self.scroll_x.pack(side="bottom", fill="x")

        self.editor = tk.Text(
            cuerpo, wrap="none", undo=True, maxundo=-1, bg=BG, fg=TEXTO, font=self.f_editor,
            insertbackground="#aeafad", insertwidth=2, selectbackground=SELECCION,
            inactiveselectbackground="#3a3d41", relief="flat", bd=0, padx=10, pady=8,
            spacing1=3, spacing3=3, highlightthickness=0, tabs=("1c",),
        )
        self.editor.pack(side="left", fill="both", expand=True)
        self.editor.configure(yscrollcommand=self._on_yscroll, xscrollcommand=self.scroll_x.set)
        self.scroll_y.configure(command=self.editor.yview)
        self.scroll_x.configure(command=self.editor.xview)

        self._configurar_tags(self.editor)
        self.editor.tag_configure("linea_actual", background=LINEA_ACTUAL)
        self.editor.tag_configure("linea_error", background=LINEA_ERROR)
        self.editor.tag_configure("error_pos", underline=True)
        self.editor.tag_lower("linea_actual")
        self.editor.tag_lower("linea_error")
        self.editor.tag_raise("sel")

        self.editor.bind("<KeyRelease>", lambda _e: self._despues_de_editar())
        self.editor.bind("<ButtonRelease-1>", lambda _e: self._actualizar_cursor())
        self.editor.bind("<<Modified>>", self._on_modificado)
        self.editor.bind("<Return>", self._on_return)
        self.editor.bind("<Tab>", self._on_tab)
        self.editor.bind("<Control-slash>", self._on_comentar)
        self.editor.bind("<Control-MouseWheel>", self._on_ctrl_rueda)
        self.editor.bind("<Control-Return>", lambda _e: (self.ejecutar(), "break")[1])
        self.editor.bind("<Configure>", lambda _e: self._dibujar_gutter())
        return marco

    def _configurar_tags(self, widget: tk.Text) -> None:
        for nombre, color in COLORES_SINTAXIS.items():
            widget.tag_configure(nombre, foreground=color)
        widget.tag_configure("comentario", foreground=COLORES_SINTAXIS["comentario"], font=self._cursiva(widget))

    def _cursiva(self, widget: tk.Text):
        f = tkfont.Font(font=widget.cget("font"))
        f.configure(slant="italic")
        self._fuentes_extra = getattr(self, "_fuentes_extra", []) + [f]
        return f

    # --- panel inferior ---------------------------------------------------

    def _texto_con_scroll(self, padre, fuente=None) -> tk.Text:
        contenedor = tk.Frame(padre, bg=BG)
        contenedor.pack(fill="both", expand=True)
        texto = tk.Text(contenedor, wrap="none", bg=BG, fg=TEXTO, font=fuente or self.f_panel, relief="flat", bd=0,
                        padx=14, pady=10, spacing1=2, spacing3=2, highlightthickness=0,
                        insertbackground=TEXTO, selectbackground=SELECCION, state="disabled")
        sy = ttk.Scrollbar(contenedor, orient="vertical", command=texto.yview)
        sx = ttk.Scrollbar(contenedor, orient="horizontal", command=texto.xview)
        texto.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        texto.pack(side="left", fill="both", expand=True)
        self._configurar_tags(texto)
        texto.tag_configure("titulo", foreground="#4fc1ff", font=self._negrita_panel())
        texto.tag_configure("env", foreground="#dcdcaa")
        texto.tag_configure("ok", foreground="#89d185")
        texto.tag_configure("fallo", foreground="#f48771")
        texto.tag_configure("tenue", foreground=TEXTO_TENUE)
        texto.tag_configure("plan", foreground="#c586c0")
        return texto

    def _negrita_panel(self):
        f = tkfont.Font(font=self.f_panel)
        f.configure(weight="bold")
        self._fuentes_extra = getattr(self, "_fuentes_extra", []) + [f]
        return f

    def _tabla(self, padre, columnas, estilo: str | None = None) -> ttk.Treeview:
        contenedor = tk.Frame(padre, bg=BG)
        contenedor.pack(fill="both", expand=True)
        tabla = ttk.Treeview(contenedor, columns=columnas, show="headings", selectmode="browse",
                             **({"style": estilo} if estilo else {}))
        sy = ttk.Scrollbar(contenedor, orient="vertical", command=tabla.yview)
        sx = ttk.Scrollbar(contenedor, orient="horizontal", command=tabla.xview)
        tabla.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        tabla.pack(side="left", fill="both", expand=True)
        return tabla

    def _construir_panel(self, padre) -> tk.Frame:
        marco = tk.Frame(padre, bg=BG)
        self.tabs = ttk.Notebook(marco)
        self.tabs.pack(fill="both", expand=True)

        self.pestanas: dict[str, tk.Frame] = {}
        for clave, titulo in (("resultados", "RESULTADOS"), ("mensajes", "MENSAJES"), ("problemas", "PROBLEMAS"),
                              ("tokens", "TOKENS"), ("arbol", "ÁRBOL SINTÁCTICO"), ("ast", "AST"),
                              ("bateria", "BATERÍA")):
            frame = tk.Frame(self.tabs, bg=BG)
            self.tabs.add(frame, text=titulo)
            self.pestanas[clave] = frame

        self._construir_resultados()
        self.texto_mensajes = self._texto_con_scroll(self.pestanas["mensajes"])
        self._escribir(self.texto_mensajes, "Presione F5 para ejecutar el script (F6 solo lo analiza).", "tenue")
        self._construir_problemas()
        self._construir_tokens()
        self.visores = {"arbol": VisorImagen(self, self.pestanas["arbol"]),
                        "ast": VisorImagen(self, self.pestanas["ast"])}
        for visor in self.visores.values():
            visor.limpiar("Analice o ejecute el script (F6 / F5) para ver el árbol.")
        self.texto_bateria = self._texto_con_scroll(self.pestanas["bateria"])
        self.tabs.bind("<<NotebookTabChanged>>", self._on_cambio_pestana)
        return marco

    def _construir_resultados(self) -> None:
        division = tk.PanedWindow(self.pestanas["resultados"], orient="horizontal", bg=BORDE, bd=0, sashwidth=3,
                                  sashrelief="flat")
        division.pack(fill="both", expand=True)

        izquierda = tk.Frame(division, bg=BG)
        self.lista_sentencias = self._tabla(izquierda, ("num", "sentencia", "estado"))
        for col, texto, ancho, ancla in (("num", "#", 44, "center"), ("sentencia", "SENTENCIA", 150, "w"),
                                         ("estado", "RESULTADO", 150, "w")):
            self.lista_sentencias.heading(col, text=texto)
            self.lista_sentencias.column(col, width=ancho, anchor=ancla, stretch=(col == "estado"))
        self.lista_sentencias.tag_configure("ok", foreground="#89d185")
        self.lista_sentencias.tag_configure("consulta", foreground="#4fc1ff")
        self.lista_sentencias.tag_configure("fallo", foreground="#f48771")
        self.lista_sentencias.tag_configure("pendiente", foreground=TEXTO_TENUE)
        self.lista_sentencias.bind("<<TreeviewSelect>>", self._on_seleccionar_sentencia)
        self.lista_sentencias.bind("<Double-1>", self._on_ir_a_sentencia)
        division.add(izquierda, minsize=220, width=360)

        derecha = tk.Frame(division, bg=BG)
        self.lbl_grilla = tk.Label(derecha, text="", bg=BG_LATERAL, fg=TEXTO_TENUE, font=self.f_tenue, anchor="w",
                                   padx=12, pady=5)
        self.lbl_grilla.pack(side="top", fill="x")
        self.contenedor_grilla = tk.Frame(derecha, bg=BG)
        self.contenedor_grilla.pack(fill="both", expand=True)
        self.grilla = self._tabla(self.contenedor_grilla, (), estilo="Grilla.Treeview")
        self.grilla.tag_configure("par", background=BG)
        self.grilla.tag_configure("impar", background=BG_FILA_ALT)
        self.lbl_mensaje = tk.Label(self.contenedor_grilla, text="", bg=BG, fg=TEXTO, font=self.f_ui,
                                    justify="left", anchor="nw", padx=18, pady=16)
        division.add(derecha, minsize=300)
        self._mostrar_mensaje_resultado("Los resultados de cada sentencia aparecen aquí.", tenue=True)

    def _construir_problemas(self) -> None:
        columnas = ("linea", "columna", "fase", "categoria", "mensaje")
        self.tabla_errores = self._tabla(self.pestanas["problemas"], columnas)
        for col, texto, ancho, ancla in (("linea", "LÍNEA", 70, "center"), ("columna", "COL", 60, "center"),
                                         ("fase", "TIPO", 110, "center"), ("categoria", "CATEGORÍA", 110, "center"),
                                         ("mensaje", "MENSAJE", 800, "w")):
            self.tabla_errores.heading(col, text=texto)
            self.tabla_errores.column(col, width=ancho, anchor=ancla, stretch=(col == "mensaje"))
        self.tabla_errores.tag_configure("error", foreground="#f48771")
        self.tabla_errores.tag_configure("ejecucion", foreground="#cca700")
        self.tabla_errores.bind("<Double-1>", self._on_doble_clic_error)
        self.tabla_errores.bind("<Return>", self._on_doble_clic_error)

    def _construir_tokens(self) -> None:
        columnas = ("num", "tipo", "lexema", "linea", "columna")
        self.tabla_tokens = self._tabla(self.pestanas["tokens"], columnas, estilo="Grilla.Treeview")
        for col, texto, ancho, ancla in (("num", "#", 60, "center"), ("tipo", "TOKEN", 170, "w"),
                                         ("lexema", "LEXEMA", 420, "w"), ("linea", "LÍNEA", 80, "center"),
                                         ("columna", "COL", 70, "center")):
            self.tabla_tokens.heading(col, text=texto)
            self.tabla_tokens.column(col, width=ancho, anchor=ancla, stretch=(col == "lexema"))
        for tag, color in (("kw", "#569cd6"), ("lit", "#ce9178"), ("num", "#b5cea8"), ("id", "#9cdcfe"),
                           ("sim", TEXTO)):
            self.tabla_tokens.tag_configure(tag, foreground=color)
        self.tabla_tokens.bind("<Double-1>", self._on_doble_clic_token)

    # ------------------------------------------------------------------
    # Atajos
    # ------------------------------------------------------------------

    def _atar_atajos(self) -> None:
        self.bind("<F5>", lambda _e: self.ejecutar())
        self.bind("<F6>", lambda _e: self.analizar())
        self.bind("<F7>", lambda _e: self.correr_bateria())
        self.bind("<Control-s>", lambda _e: self.guardar_archivo())
        self.bind("<Control-o>", lambda _e: self.abrir_archivo())
        for tecla in ("<Control-plus>", "<Control-equal>", "<Control-KP_Add>"):
            self.bind(tecla, lambda _e: self._zoom_editor(1))
        for tecla in ("<Control-minus>", "<Control-KP_Subtract>"):
            self.bind(tecla, lambda _e: self._zoom_editor(-1))
        self.bind("<Control-0>", lambda _e: self._zoom_editor(0))

    # ------------------------------------------------------------------
    # Edicion: gutter, resaltado, cursor, atajos de texto
    # ------------------------------------------------------------------

    def _on_yscroll(self, primero, ultimo) -> None:
        self.scroll_y.set(primero, ultimo)
        self._dibujar_gutter()

    def _dibujar_gutter(self) -> None:
        g = self.gutter
        g.delete("all")
        total = int(self.editor.index("end-1c").split(".")[0])
        ancho = self.f_editor.measure("0") * max(3, len(str(total))) + 34
        if int(g.cget("width")) != ancho:
            g.configure(width=ancho)
        actual = int(self.editor.index("insert").split(".")[0])
        n = int(self.editor.index("@0,0").split(".")[0])
        while n <= total:
            info = self.editor.dlineinfo(f"{n}.0")
            if info is None:
                break
            y, alto = info[1], info[3]
            if y + alto > self.editor.winfo_height() - 2:
                break
            color = "#c6c6c6" if n == actual else TEXTO_TENUE
            g.create_text(ancho - 14, y + alto / 2, anchor="e", text=str(n), fill=color, font=self.f_editor)
            if n in self.lineas_error:
                g.create_oval(9, y + alto / 2 - 5, 19, y + alto / 2 + 5, fill="#f14c4c", outline="")
            n += 1

    def _despues_de_editar(self) -> None:
        self._actualizar_cursor()
        if self._job_resaltado is not None:
            self.after_cancel(self._job_resaltado)
        self._job_resaltado = self.after(90, self._resaltar_editor)

    def _actualizar_cursor(self) -> None:
        linea, col = self.editor.index("insert").split(".")
        self.lbl_posicion.configure(text=f"Ln {linea}, Col {int(col) + 1}")
        self.editor.tag_remove("linea_actual", "1.0", "end")
        self.editor.tag_add("linea_actual", "insert linestart", "insert lineend+1c")
        self._dibujar_gutter()

    def _resaltar_editor(self) -> None:
        self._job_resaltado = None
        cat = self.db.catalogo
        tablas = set(cat.tablas)
        columnas = {c.nombre for t in cat.tablas.values() for c in t.columnas}
        self._resaltar(self.editor, RE_FUENTE, lambda m, t: self._clasificar_fuente(m, t, tablas, columnas))

    @staticmethod
    def _clasificar_fuente(m: re.Match, texto: str, tablas: set[str], columnas: set[str]) -> str | None:
        tipo = m.lastgroup
        if tipo != "palabra":
            return tipo
        palabra = m.group()
        mayus = palabra.upper()
        if mayus in SENTENCIAS:
            return "kw_ctrl"
        if mayus in FUNCIONES:
            return "funcion"
        if mayus in KW:
            return "kw"
        if mayus in TIPOS:
            return "tipo"
        if mayus in CONSTANTES:
            return "const"
        minus = palabra.lower()
        if minus in tablas:
            return "tabla"
        if minus in columnas:
            return "columna"
        return None

    def _resaltar(self, widget: tk.Text, patron: re.Pattern, clasificar) -> None:
        texto = widget.get("1.0", "end-1c")
        for nombre in COLORES_SINTAXIS:
            widget.tag_remove(nombre, "1.0", "end")
        inicios = [0]
        for m in re.finditer(r"\n", texto):
            inicios.append(m.end())

        def idx(offset: int) -> str:
            linea = bisect.bisect_right(inicios, offset) - 1
            return f"{linea + 1}.{offset - inicios[linea]}"

        rangos: dict[str, list[str]] = {}
        for m in patron.finditer(texto):
            tag = clasificar(m, texto)
            if tag:
                rangos.setdefault(tag, []).extend((idx(m.start()), idx(m.end())))
        for tag, indices in rangos.items():
            widget.tag_add(tag, *indices)

    def _on_modificado(self, _evento=None) -> None:
        if self.editor.edit_modified():
            self.modificado = True
            self._actualizar_titulo()
            self.editor.edit_modified(False)

    def _on_return(self, _evento) -> str:
        e = self.editor
        antes = e.get("insert linestart", "insert")
        despues = e.get("insert", "insert lineend")
        sangria = re.match(r"[ \t]*", antes).group()
        abre = antes.rstrip().endswith("(")
        e.insert("insert", "\n" + sangria + ("    " if abre else ""))
        if abre and despues.strip().startswith(")"):
            pos = e.index("insert")
            e.insert("insert", "\n" + sangria)
            e.mark_set("insert", pos)
        e.see("insert")
        self._despues_de_editar()
        return "break"

    def _on_tab(self, _evento) -> str:
        self.editor.insert("insert", "    ")
        return "break"

    def _on_comentar(self, _evento) -> str:
        e = self.editor
        try:
            inicio, fin = e.index("sel.first linestart"), e.index("sel.last")
        except tk.TclError:
            inicio, fin = e.index("insert linestart"), e.index("insert")
        primera = int(inicio.split(".")[0])
        ultima = int(fin.split(".")[0])
        lineas = range(primera, ultima + 1)
        todas = all(e.get(f"{n}.0", f"{n}.end").lstrip().startswith("--") for n in lineas)
        for n in lineas:
            texto = e.get(f"{n}.0", f"{n}.end")
            if todas:
                nuevo = re.sub(r"^(\s*)-- ?", r"\1", texto, count=1)
            else:
                nuevo = re.sub(r"^(\s*)", r"\1-- ", texto, count=1)
            e.delete(f"{n}.0", f"{n}.end")
            e.insert(f"{n}.0", nuevo)
        self._despues_de_editar()
        return "break"

    # --- zoom -----------------------------------------------------------

    def _on_ctrl_rueda(self, evento) -> str:
        self._zoom_editor(1 if evento.delta > 0 else -1)
        return "break"

    def _zoom_editor(self, paso: int) -> None:
        tam = 15 if paso == 0 else max(9, min(34, int(self.f_editor.cget("size")) + paso))
        self.f_editor.configure(size=tam)
        self.f_panel.configure(size=max(9, tam - 2))
        self.f_grilla.configure(size=max(9, tam - 3))
        ttk.Style(self).configure("Grilla.Treeview", rowheight=self.f_grilla.metrics("linespace") + 8)
        self._actualizar_zoom_label()
        self._dibujar_gutter()

    def _actualizar_zoom_label(self) -> None:
        self.lbl_zoom.configure(text=f"Fuente {self.f_editor.cget('size')}")

    def _actualizar_bd_label(self) -> None:
        self.lbl_bd.configure(text=f"BD: {self.db.nombre}   ")

    # ------------------------------------------------------------------
    # Titulo / pestana del archivo
    # ------------------------------------------------------------------

    def _actualizar_titulo(self) -> None:
        nombre = self.ruta_actual.name if self.ruta_actual else "sin_titulo.sql"
        punto = "  ●" if self.modificado else ""
        self.lbl_tab.configure(text=f"▦  {nombre}{punto}")
        self.title(f"{nombre}{' ●' if self.modificado else ''} - Intérprete SQL")

    # ------------------------------------------------------------------
    # abrir / guardar / base de datos
    # ------------------------------------------------------------------

    def abrir_archivo(self) -> None:
        ruta = filedialog.askopenfilename(filetypes=[("SQL", "*.sql"), ("Todos", "*.*")])
        if ruta:
            self.cargar_archivo(ruta)

    def cargar_archivo(self, ruta: str | pathlib.Path) -> None:
        ruta = pathlib.Path(ruta)
        try:
            contenido = ruta.read_text(encoding="utf-8")
        except OSError as error:
            messagebox.showerror("No se pudo abrir", str(error))
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", contenido)
        self.editor.edit_reset()
        self.editor.edit_modified(False)
        self.ruta_actual = ruta
        self.modificado = False
        self._limpiar_marcas_error()
        self.editor.mark_set("insert", "1.0")
        self._despues_de_editar()
        self._actualizar_titulo()
        self._estado("  Archivo abierto", AZUL)

    def guardar_archivo(self) -> None:
        if self.ruta_actual is None:
            self.guardar_como()
            return
        self._escribir_a_disco(self.ruta_actual)

    def guardar_como(self) -> None:
        ruta = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL", "*.sql")])
        if ruta:
            self.ruta_actual = pathlib.Path(ruta)
            self._escribir_a_disco(self.ruta_actual)

    def _escribir_a_disco(self, ruta: str | pathlib.Path) -> None:
        contenido = self.editor.get("1.0", "end-1c")
        try:
            pathlib.Path(ruta).write_text(contenido, encoding="utf-8")
        except OSError as error:
            messagebox.showerror("No se pudo guardar", str(error))
            return
        self.modificado = False
        self._actualizar_titulo()
        self._estado("  Guardado", AZUL)

    def elegir_base(self) -> None:
        ruta = filedialog.askdirectory(title="Carpeta de la base de datos (se crea si está vacía)",
                                       initialdir=str(self.db.ruta.parent))
        if not ruta:
            return
        try:
            self.db = Database(ruta)
        except (OSError, ValueError) as error:
            messagebox.showerror("Base de datos inválida", str(error))
            return
        self._actualizar_bd_label()
        self._poblar_bd()
        self._resaltar_editor()
        self._estado(f"  Base de datos: {self.db.ruta}", AZUL)

    # ------------------------------------------------------------------
    # analizar y ejecutar
    # ------------------------------------------------------------------

    def _estado(self, texto: str, color: str) -> None:
        self.barra_estado.configure(bg=color)
        for w in self.barra_estado.winfo_children():
            w.configure(bg=color)
        self.lbl_estado.configure(text=texto)

    def _escribir(self, widget: tk.Text, texto: str, tag: str | None = None, limpiar: bool = True) -> None:
        widget.configure(state="normal")
        if limpiar:
            widget.delete("1.0", "end")
        widget.insert("end", texto, tag) if tag else widget.insert("end", texto)
        widget.configure(state="disabled")

    def _seleccionar_pestana(self, clave: str) -> None:
        self.tabs.select(self.pestanas[clave])

    def _fuente(self) -> tuple[str, bool]:
        """Texto a procesar: la seleccion (con el resto en blanco, para conservar lineas y columnas) o todo."""
        completo = self.editor.get("1.0", "end-1c")
        try:
            inicio, fin = self.editor.index("sel.first"), self.editor.index("sel.last")
        except tk.TclError:
            return completo, False
        a = len(self.editor.get("1.0", inicio))
        b = len(self.editor.get("1.0", fin))
        if a == b:
            return completo, False
        en_blanco = lambda s: re.sub(r"[^\n]", " ", s)  # noqa: E731
        return en_blanco(completo[:a]) + completo[a:b] + en_blanco(completo[b:]), True

    def analizar(self) -> None:
        self._procesar(ejecutar=False)

    def ejecutar(self) -> None:
        self._procesar(ejecutar=True)

    def _procesar(self, ejecutar: bool) -> None:
        fuente, seleccion = self._fuente()
        try:
            self.db.recargar()
        except ValueError as error:
            messagebox.showerror("metadata.txt inválido", str(error))
            return
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            self.resultado = analizar(fuente, self.db, ejecutar=ejecutar)
        finally:
            self.config(cursor="")
        r = self.resultado
        self._pintar_errores()
        self._pintar_tokens()
        self._arboles_pendientes = {"arbol", "ast"}
        for visor in self.visores.values():
            visor.limpiar("Generando…")
        self._pintar_resultados()
        self._pintar_mensajes(seleccion)
        if ejecutar:
            self._poblar_bd()
            self._resaltar_editor()
        self._pintar_estado(ejecutar, seleccion)

        if r.errores_analisis:
            destino = "problemas"
        elif ejecutar and r.ultima_consulta is not None:
            destino = "resultados"
        elif ejecutar:
            destino = "problemas" if r.errores else "mensajes"
        else:
            destino = self._pestana_actual() if self._pestana_actual() in ("tokens", "arbol", "ast") else "tokens"
        self._seleccionar_pestana(destino)
        self._on_cambio_pestana()

    def _pestana_actual(self) -> str | None:
        actual = self.tabs.select()
        return next((k for k, f in self.pestanas.items() if str(f) == actual), None)

    # ------------------------------------------------------------------
    # paneles
    # ------------------------------------------------------------------

    def _limpiar_marcas_error(self) -> None:
        self.lineas_error = set()
        self.editor.tag_remove("linea_error", "1.0", "end")
        self.editor.tag_remove("error_pos", "1.0", "end")

    def _pintar_errores(self) -> None:
        self.tabla_errores.delete(*self.tabla_errores.get_children())
        self._limpiar_marcas_error()
        r = self.resultado
        if r is None:
            return
        for error in r.errores:
            tag = "ejecucion" if error.fase == "ejecucion" else "error"
            self.tabla_errores.insert("", "end", values=(error.line, error.column, NOMBRE_FASE[error.fase],
                                                         error.category, error.message), tags=(tag,))
            self.lineas_error.add(error.line)
            self.editor.tag_add("linea_error", f"{error.line}.0", f"{error.line}.end+1c")
            inicio = f"{error.line}.{max(error.column - 1, 0)}"
            self.editor.tag_add("error_pos", inicio, f"{inicio} wordend")
        n = len(r.errores)
        self.tabs.tab(self.pestanas["problemas"], text=f"PROBLEMAS  {n}" if n else "PROBLEMAS")
        self._dibujar_gutter()

    def _ir_a(self, linea, columna) -> None:
        self.editor.mark_set("insert", f"{linea}.{max(int(columna) - 1, 0)}")
        self.editor.see(f"{linea}.0")
        self.editor.focus_set()
        self._despues_de_editar()

    def _on_doble_clic_error(self, _evento=None) -> None:
        seleccion = self.tabla_errores.selection()
        if seleccion:
            self._ir_a(*self.tabla_errores.item(seleccion[0], "values")[:2])

    def _on_doble_clic_token(self, _evento=None) -> None:
        seleccion = self.tabla_tokens.selection()
        if seleccion:
            valores = self.tabla_tokens.item(seleccion[0], "values")
            self._ir_a(valores[3], valores[4])

    def _pintar_tokens(self) -> None:
        t = self.tabla_tokens
        t.delete(*t.get_children())
        r = self.resultado
        if r is None:
            return
        for i, tok in enumerate(r.tokens, start=1):
            if tok.tipo in ("INT_LIT", "FLOAT_LIT"):
                tag = "num"
            elif tok.tipo == "STRING_LIT":
                tag = "lit"
            elif tok.tipo == "IDENTIFIER":
                tag = "id"
            elif tok.tipo.isalpha() and tok.lexema.isalpha():
                tag = "kw"
            else:
                tag = "sim"
            t.insert("", "end", values=(i, tok.tipo, tok.lexema, tok.linea, tok.columna), tags=(tag,))
        self.tabs.tab(self.pestanas["tokens"], text=f"TOKENS  {len(r.tokens)}")

    def _on_cambio_pestana(self, _evento=None) -> None:
        clave = self._pestana_actual()
        if clave in self._arboles_pendientes:
            self._arboles_pendientes.discard(clave)
            self.after(10, lambda: self._pintar_arbol(clave))

    def _pintar_arbol(self, clave: str) -> None:
        r = self.resultado
        visor = self.visores[clave]
        if r is None:
            return
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            if clave == "arbol":
                if r.tree is None:
                    visor.limpiar("Sin árbol sintáctico.")
                    return
                info = "Reglas de la gramática (azul) y tokens (amarillo)"
                if dot_disponible():
                    try:
                        visor.mostrar_png(parse_tree_png(r.tree, r.parser.ruleNames, MAX_NODOS_ARBOL), info)
                        return
                    except Exception:  # noqa: BLE001 - cae al texto
                        pass
                visor.mostrar_texto(parse_tree_texto(r.tree, r.parser), "Graphviz no disponible: vista en texto")
            else:
                if r.ast is None:
                    visor.limpiar("No hay AST: corrija primero los errores léxicos/sintácticos (pestaña PROBLEMAS).")
                    return
                info = "Sentencias (azul), columnas (verde), literales (amarillo), agregaciones (naranja); ⟨tipo⟩ inferido"
                if dot_disponible():
                    try:
                        visor.mostrar_png(ast_png(r.ast, MAX_NODOS_ARBOL), info)
                        return
                    except Exception:  # noqa: BLE001 - cae al texto
                        pass
                visor.mostrar_texto(ast_texto(r.ast), "Graphviz no disponible: vista en texto")
        finally:
            self.config(cursor="")

    # --- resultados -------------------------------------------------------

    def _pintar_resultados(self) -> None:
        lista = self.lista_sentencias
        lista.delete(*lista.get_children())
        self._resultados_por_iid.clear()
        r = self.resultado
        if r is None:
            return
        if not r.ejecutado:
            n = len(r.ast.sentencias) if r.ast is not None else 0
            texto = ("Análisis correcto. Presione F5 para ejecutar." if r.ok and n else
                     "No se ejecutó nada: corrija los problemas primero (pestaña PROBLEMAS)." if not r.ok else
                     "No hay sentencias.")
            self._mostrar_mensaje_resultado(texto, tenue=r.ok)
            if r.ast is not None:
                for i, s in enumerate(r.ast.sentencias, start=1):
                    lista.insert("", "end", values=(i, _primera_linea(s.texto), "sin ejecutar"), tags=("pendiente",))
            return

        seleccionar = None
        for res in r.resultados:
            if res.error is not None:
                estado, tag = f"✖ {res.error.message}", "fallo"
            elif res.es_consulta:
                estado, tag = f"✔ {len(res.filas)} fila(s)", "consulta"
            else:
                estado, tag = f"✔ {res.mensaje}", "ok"
            iid = lista.insert("", "end", values=(res.numero, _primera_linea(res.texto), estado), tags=(tag,))
            self._resultados_por_iid[iid] = res
            if res.es_consulta and res.ok or res.error is not None:
                seleccionar = iid
        for s in r.ast.sentencias[len(r.resultados):]:
            lista.insert("", "end", values=("", _primera_linea(s.texto), "no ejecutada"), tags=("pendiente",))
        if seleccionar is None and lista.get_children():
            seleccionar = lista.get_children()[len(r.resultados) - 1] if r.resultados else None
        if seleccionar is not None:
            lista.selection_set(seleccionar)
            lista.see(seleccionar)
            self._on_seleccionar_sentencia()

    def _on_seleccionar_sentencia(self, _evento=None) -> None:
        seleccion = self.lista_sentencias.selection()
        if not seleccion or seleccion[0] not in self._resultados_por_iid:
            return
        res = self._resultados_por_iid[seleccion[0]]
        if res.error is not None:
            self._mostrar_mensaje_resultado(f"✖  Error en la sentencia {res.numero} (línea {res.error.line}):\n\n"
                                            f"{res.error.message}", color="#f48771")
        elif res.es_consulta:
            self._mostrar_grilla(res)
        else:
            plan = "\n".join(f"   • {p}" for p in res.plan)
            self._mostrar_mensaje_resultado(f"✔  {res.mensaje}\n\n{res.tiempo_ms:.1f} ms" +
                                            (f"\n\nPlan:\n{plan}" if plan else ""), color="#89d185")

    def _on_ir_a_sentencia(self, _evento=None) -> None:
        seleccion = self.lista_sentencias.selection()
        if seleccion and seleccion[0] in self._resultados_por_iid:
            self._ir_a(self._resultados_por_iid[seleccion[0]].linea, 1)

    def _mostrar_mensaje_resultado(self, texto: str, color: str = TEXTO, tenue: bool = False) -> None:
        self.grilla.master.pack_forget()
        self.lbl_grilla.configure(text="")
        self.lbl_mensaje.configure(text=texto, fg=TEXTO_TENUE if tenue else color,
                                   wraplength=max(self.contenedor_grilla.winfo_width() - 40, 400))
        self.lbl_mensaje.pack(fill="both", expand=True)

    def _mostrar_grilla(self, res, titulo: str | None = None) -> None:
        self.lbl_mensaje.pack_forget()
        self.grilla.master.pack(fill="both", expand=True)
        g = self.grilla
        g.delete(*g.get_children())
        ids = [f"c{i}" for i in range(len(res.columnas))]
        g.configure(columns=ids)
        filas = res.filas_texto()
        self._filas_grilla = list(zip(res.filas, filas))
        self._orden_grilla = None
        for i, (col, cid) in enumerate(zip(res.columnas, ids)):
            tipo = res.tipos[i] if res.tipos else ""
            g.heading(cid, text=f"{col}  ·  {tipo}" if tipo else col, command=lambda k=i: self._ordenar_grilla(k))
            muestra = [col + "  ·  " + tipo] + [f[i] for f in filas[:200]]
            ancho = min(max(self.f_grilla.measure(t) for t in muestra) + 28, 420)
            numerico = tipo in ("INT", "FLOAT")
            g.column(cid, width=max(ancho, 70), anchor="e" if numerico else "w", stretch=False)
        self._llenar_grilla()
        total = len(res.filas)
        partes = [titulo or f"Sentencia {res.numero}", f"{total} fila(s)", f"{len(res.columnas)} columna(s)",
                  f"{res.tiempo_ms:.1f} ms"]
        if total > MAX_FILAS_GRILLA:
            partes.append(f"se muestran {MAX_FILAS_GRILLA}")
        if res.plan:
            partes.append("plan: " + "  |  ".join(res.plan))
        self.lbl_grilla.configure(text="   ·   ".join(partes))

    def _llenar_grilla(self) -> None:
        g = self.grilla
        g.delete(*g.get_children())
        for i, (_crudas, textos) in enumerate(self._filas_grilla[:MAX_FILAS_GRILLA]):
            g.insert("", "end", values=textos, tags=("par" if i % 2 == 0 else "impar",))

    def _ordenar_grilla(self, columna: int) -> None:
        descendente = self._orden_grilla == (columna, False)
        self._orden_grilla = (columna, descendente)
        self._filas_grilla.sort(key=lambda par: (0,) if par[0][columna] is None else (1, par[0][columna]),
                                reverse=descendente)
        self._llenar_grilla()

    # --- mensajes ---------------------------------------------------------

    def _pintar_mensajes(self, seleccion: bool) -> None:
        t = self.texto_mensajes
        r = self.resultado
        self._escribir(t, "")
        if r is None:
            return
        origen = "selección" if seleccion else (self.ruta_actual.name if self.ruta_actual else "editor")
        if not r.ejecutado:
            n = len(r.ast.sentencias) if r.ast is not None else 0
            self._escribir(t, f"▶ Análisis ({origen}) sobre la base '{self.db.nombre}'\n\n", "titulo", limpiar=False)
            if r.errores_analisis:
                self._escribir(t, f"✖ {len(r.errores_analisis)} error(es); no se ejecutó nada.\n", "fallo",
                               limpiar=False)
                for e in r.errores_analisis:
                    self._escribir(t, f"   línea {e.line}:{e.column}  [{NOMBRE_FASE[e.fase]} / {e.category}]  "
                                      f"{e.message}\n", "tenue", limpiar=False)
            else:
                self._escribir(t, f"✔ {len(r.tokens)} tokens, {n} sentencia(s), 0 errores léxicos, sintácticos o "
                                  "semánticos.\n", "ok", limpiar=False)
            return

        self._escribir(t, f"▶ Ejecución ({origen}) sobre la base '{self.db.nombre}'  —  {self.db.ruta}\n\n", "titulo",
                       limpiar=False)
        for res in r.resultados:
            self._escribir(t, f"[{res.numero}] {res.tipo}  ", "env", limpiar=False)
            self._escribir(t, f"(línea {res.linea}, {res.tiempo_ms:.1f} ms)\n", "tenue", limpiar=False)
            if res.error is not None:
                self._escribir(t, f"    ✖ {res.error.message}\n", "fallo", limpiar=False)
            else:
                self._escribir(t, f"    ✔ {res.mensaje}\n", "ok", limpiar=False)
            for nota in res.plan:
                self._escribir(t, f"      plan: {nota}\n", "plan", limpiar=False)
            self._escribir(t, "\n", limpiar=False)
        pendientes = len(r.ast.sentencias) - len(r.resultados)
        if pendientes:
            self._escribir(t, f"Se detuvo la ejecución: {pendientes} sentencia(s) no se ejecutaron.\n", "fallo",
                           limpiar=False)

    def _pintar_estado(self, ejecutar: bool, seleccion: bool) -> None:
        r = self.resultado
        if r is None:
            return
        sufijo = " (selección)" if seleccion else ""
        if r.errores_analisis:
            n = len(r.errores_analisis)
            self._estado(f"  ✖ {n} problema{'s' if n != 1 else ''}{sufijo}", ROJO)
        elif not ejecutar:
            n = len(r.ast.sentencias)
            self._estado(f"  ✔ Análisis correcto: {n} sentencia(s){sufijo}", VERDE)
        elif r.errores_ejecucion:
            self._estado(f"  ✖ Error de ejecución en la sentencia {len(r.resultados)}{sufijo}", ROJO)
        else:
            total = sum(res.tiempo_ms for res in r.resultados)
            self._estado(f"  ✔ {len(r.resultados)} sentencia(s) ejecutada(s) en {total:.0f} ms{sufijo}", VERDE)

    # --- bateria ----------------------------------------------------------

    def correr_bateria(self) -> None:
        self._estado("  Ejecutando batería de pruebas...", "#6c4a00")
        self.config(cursor="watch")
        self.update_idletasks()
        try:
            resultados = ejecutar_bateria()
        finally:
            self.config(cursor="")
        pasaron = sum(1 for r in resultados if r.paso)
        total = len(resultados)

        t = self.texto_bateria
        self._escribir(t, f"✔ {pasaron}/{total} pruebas pasaron\n", "ok" if pasaron == total else "fallo")
        self._escribir(t, f"{total - pasaron} fallida(s)   ·   cada caso corre sobre una base de datos temporal\n\n",
                       "tenue", limpiar=False)
        for r in resultados:
            marca, tag = ("✔", "ok") if r.paso else ("✖", "fallo")
            ruta = r.archivo.relative_to(RAIZ_PRUEBAS).as_posix()
            self._escribir(t, f"{marca} {ruta}", tag, limpiar=False)
            self._escribir(t, f"   {r.caso}\n", "tenue", limpiar=False)
            if not r.paso:
                self._escribir(t, f"     {r.razon}\n", "fallo", limpiar=False)
        self._estado(f"  Batería: {pasaron}/{total} pasaron", VERDE if pasaron == total else ROJO)
        self._seleccionar_pestana("bateria")


def _primera_linea(texto: str) -> str:
    """Primera linea con contenido de la sentencia (sin comentarios), recortada."""
    for linea in texto.splitlines():
        limpia = linea.strip()
        if limpia and not limpia.startswith("--"):
            return limpia if len(limpia) <= 60 else limpia[:57] + "..."
    return texto.strip()[:60]


def main() -> None:
    app = SQLIDE()
    app.mainloop()


if __name__ == "__main__":
    main()
