"""Pruebas parciales del componente `construir_prompt` (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio.cadena import construir_prompt


def test_el_prompt_incluye_la_pregunta_y_el_contexto():
    fragmentos = [{"fuente": "reglamento_asistencia.md", "texto": "Asistencia mínima 85 %."}]
    prompt = construir_prompt("¿Cuál es la asistencia mínima?", fragmentos)
    assert "Asistencia mínima 85 %." in prompt
    assert "Pregunta: ¿Cuál es la asistencia mínima?" in prompt


def test_varios_fragmentos_van_uno_por_linea():
    fragmentos = [
        {"fuente": "a.md", "texto": "Primer dato."},
        {"fuente": "b.md", "texto": "Segundo dato."},
    ]
    prompt = construir_prompt("Pregunta", fragmentos)
    assert "- Primer dato.\n- Segundo dato." in prompt


def test_contexto_vacio_mantiene_estructura_valida():
    prompt = construir_prompt("¿Sin contexto?", [])
    assert "Contexto:\n\nPregunta: ¿Sin contexto?" in prompt


def test_contrato_prompt_es_texto():
    prompt = construir_prompt("Hola", [{"fuente": "a.md", "texto": "Dato."}])
    assert isinstance(prompt, str)
