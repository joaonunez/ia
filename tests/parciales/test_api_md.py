"""Pruebas parciales de la generación de referencia API `docs/api.md` (U3.6 · Bloque 45)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import ejemplos_api  # noqa: E402
import generar_api_md  # noqa: E402


def test_ejemplos_api_no_contienen_respuestas_estaticas():
    assert len(ejemplos_api.EJEMPLOS) >= 5
    for ej in ejemplos_api.EJEMPLOS:
        assert "respuesta" not in ej
        assert ej["metodo"] in ("GET", "POST")


def test_generar_api_md_es_determinista_y_cubre_endpoints():
    md1 = generar_api_md.generar_markdown()
    md2 = generar_api_md.generar_markdown()
    assert md1 == md2
    assert "/health" in md1
    assert "/ask" in md1
    assert "/estudiantes/{nombre}" in md1
    assert "85 %" in md1
