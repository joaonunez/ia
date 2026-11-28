"""Pruebas parciales del doble `ModeloSimulado.generar` (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio.cadena import ModeloSimulado, SIN_INFORMACION


def test_responde_con_primera_linea_del_contexto_y_cita():
    modelo = ModeloSimulado()
    prompt = (
        "Responde solo con el contexto.\n"
        "Contexto:\n"
        "- La asistencia mínima es 85 %.\n"
        "- Otro dato.\n"
        "Pregunta: ¿Cuál es la asistencia?"
    )
    assert modelo.generar(prompt) == "La asistencia mínima es 85 %. [1]"


def test_dice_que_no_sabe_si_el_contexto_esta_vacio():
    modelo = ModeloSimulado()
    prompt = "Responde solo con el contexto.\nContexto:\n\nPregunta: ¿Quién es el director?"
    assert modelo.generar(prompt) == SIN_INFORMACION


def test_contrato_respuesta_es_texto():
    modelo = ModeloSimulado()
    salida = modelo.generar("Contexto:\n- Dato.\nPregunta: P")
    assert isinstance(salida, str)
