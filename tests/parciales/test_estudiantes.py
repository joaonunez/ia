"""Pruebas parciales de `consultar_estudiante` en `servicio/logica.py` (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio.logica import consultar_estudiante


def test_estudiante_existente_devuelve_sus_datos():
    datos = consultar_estudiante("Sofía Rojas")
    assert datos is not None
    assert datos["nombre"] == "Sofía Rojas"
    assert datos["curso"] == "2°B"
    assert datos["simulado"] is True


def test_estudiante_acepta_minusculas_sin_tilde():
    assert consultar_estudiante("sofia rojas") == consultar_estudiante("Sofía Rojas")


def test_estudiante_inexistente_devuelve_none():
    assert consultar_estudiante("Estudiante Inexistente") is None


def test_nombre_vacio_devuelve_none():
    assert consultar_estudiante("   ") is None


def test_contrato_el_resultado_es_dict_o_none():
    for nombre in ("Sofía Rojas", "Diego Soto", "Estudiante Inexistente"):
        datos = consultar_estudiante(nombre)
        assert datos is None or (
            isinstance(datos, dict)
            and {"nombre", "curso", "notas", "promedio", "asistencia_pct", "inasistencias", "simulado"}.issubset(
                datos.keys()
            )
        )
