"""Pruebas parciales del README técnico y diario de fricción (U3.6 · Bloque 44)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import contar_friccion  # noqa: E402
import verificar_readme  # noqa: E402


def test_diario_friccion_tiene_filas_validas_y_secciones_en_readme():
    filas = contar_friccion.leer_filas()
    assert len(filas) >= 3
    assert contar_friccion.main(["--readme", str(REPO_ROOT / "README.md")]) == 0


def test_readme_cumple_reglas_sin_ejecutar_pytest_anidado():
    texto = verificar_readme.README.read_text(encoding="utf-8")
    for fn in (
        verificar_readme.comprobar_readme1,
        verificar_readme.comprobar_readme2,
        verificar_readme.comprobar_readme3,
        verificar_readme.comprobar_readme5,
        verificar_readme.comprobar_readme6,
        verificar_readme.comprobar_readme7,
    ):
        ok, detalle = fn(texto)
        assert ok, detalle
