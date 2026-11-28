"""Pruebas parciales del componente `recuperar` (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio.cadena import recuperar


def test_asistencia_trae_fragmento_de_reglamento_asistencia():
    fragmentos = recuperar("¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?")
    assert fragmentos
    assert fragmentos[0]["fuente"] == "reglamento_asistencia.md"
    assert "85 %" in fragmentos[0]["texto"]


def test_notas_trae_fragmento_de_reglamento_notas():
    fragmentos = recuperar("¿Cuál es la escala de calificaciones y nota mínima de aprobación?")
    assert fragmentos
    assert fragmentos[0]["fuente"] == "reglamento_notas.md"
    assert "4.0" in fragmentos[0]["texto"]


def test_pregunta_fuera_del_corpus_no_trae_nada():
    assert recuperar("¿Cómo se llama el director del establecimiento?") == []


def test_no_distingue_mayusculas_ni_tildes():
    assert recuperar("ASISTENCIA PROMOCION ESCOLAR") == recuperar("asistencia promoción escolar")


def test_contrato_cada_fragmento_tiene_fuente_y_texto():
    for pregunta in (
        "porcentaje mínimo de asistencia para promoción",
        "escala de calificaciones y nota mínima",
        "aviso formal al apoderado por riesgo de repitencia",
    ):
        for fragmento in recuperar(pregunta):
            assert set(fragmento) == {"fuente", "texto"}
            assert all(isinstance(v, str) for v in fragmento.values())
