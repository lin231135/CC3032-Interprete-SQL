"""CLI (main.py)."""

from main import main


def escribir(tmp_path, texto, nombre="s.sql"):
    ruta = tmp_path / nombre
    ruta.write_text(texto, encoding="utf-8")
    return str(ruta)


def test_cli_ejecuta_y_sale_con_0(tmp_path, capsys):
    ruta = escribir(tmp_path, "CREATE TABLE t (a INT); INSERT INTO t VALUES (7); SELECT a FROM t;")
    assert main([ruta, "--db", str(tmp_path / "bd"), "--plan"]) == 0
    salida = capsys.readouterr().out
    assert "| 7 |" in salida and "1 fila(s)" in salida and "plan:" in salida
    assert (tmp_path / "bd" / "t.csv").exists()


def test_cli_check_no_ejecuta(tmp_path, capsys):
    ruta = escribir(tmp_path, "CREATE TABLE t (a INT);")
    assert main([ruta, "--db", str(tmp_path / "bd"), "--check", "--tokens", "--ast"]) == 0
    salida = capsys.readouterr().out
    assert "Análisis correcto" in salida and "CREATE" in salida and "CreateTable" in salida
    assert not (tmp_path / "bd" / "t.csv").exists()


def test_cli_con_errores_sale_con_1(tmp_path, capsys):
    ruta = escribir(tmp_path, "SELECT * FROM fantasma;")
    assert main([ruta, "--db", str(tmp_path / "bd")]) == 1
    assert "[tabla] linea 1" in capsys.readouterr().out
