"""Pruebas parciales del medidor de guion `medir_guion.py` (U3.7 · Bloque S2)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import medir_guion as m  # noqa: E402


def test_demo_coincide_en_guion_actual():
    texto = m.GUION.read_text(encoding="utf-8")
    ok, detalle = m.demo_coincide(texto)
    assert ok, detalle


def test_demo_coincide_detecta_paso_faltante_y_titulo_distinto():
    texto = m.GUION.read_text(encoding="utf-8")
    sin_ultimo = texto.replace("- PASO-7 Una falla honesta sin modelo", "")
    ok, _ = m.demo_coincide(sin_ultimo)
    assert not ok

    cambiado = texto.replace("- PASO-1 Servicio vivo", "- PASO-1 Otro titulo")
    ok2, _ = m.demo_coincide(cambiado)
    assert not ok2

    sin_pasos = "# Guion\n\n## 4. Demo (2 min)\n\nSin pasos.\n"
    ok3, _ = m.demo_coincide(sin_pasos)
    assert not ok3


def test_reglas_guion_sin_pytest_anidado():
    texto = m.GUION.read_text(encoding="utf-8")
    for fn in (
        m.comprobar_guion1,
        m.comprobar_guion2,
        m.comprobar_guion3,
        m.comprobar_guion4,
        m.comprobar_guion6,
        m.comprobar_guion7,
        m.demo_coincide,
        m.comprobar_guion9,
    ):
        ok, detalle = fn(texto)
        assert ok, detalle
