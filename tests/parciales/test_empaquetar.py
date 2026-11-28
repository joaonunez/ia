"""Pruebas parciales del componente `empaquetar` (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio.cadena import empaquetar


def test_devuelve_texto_y_fuentes():
    texto, fuentes = empaquetar("Respuesta", [{"fuente": "reglamento_asistencia.md", "texto": "x"}])
    assert texto == "Respuesta"
    assert fuentes == ["reglamento_asistencia.md"]


def test_no_repite_fuentes_duplicadas():
    fragmentos = [
        {"fuente": "a.md", "texto": "1"},
        {"fuente": "a.md", "texto": "2"},
        {"fuente": "b.md", "texto": "3"},
    ]
    _, fuentes = empaquetar("Respuesta", fragmentos)
    assert fuentes == ["a.md", "b.md"]


def test_sin_fragmentos_devuelve_lista_vacia():
    texto, fuentes = empaquetar("Sin datos", [])
    assert texto == "Sin datos"
    assert fuentes == []


def test_contrato_fuentes_son_lista_de_textos():
    _, fuentes = empaquetar("Ok", [{"fuente": "a.md", "texto": "1"}])
    assert isinstance(fuentes, list)
    assert all(isinstance(f, str) for f in fuentes)
