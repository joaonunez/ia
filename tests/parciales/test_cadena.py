"""Pruebas de par (nivel 2) y de cadena completa con dobles (nivel 3) (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio.cadena import construir_prompt, ejecutar, recuperar


class ModeloEspia:
    """Guarda los prompts que recibe y devuelve una respuesta fija."""

    def __init__(self) -> None:
        self.prompts: list[str] = []

    def generar(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "respuesta fija"


def test_recuperar_y_construir_prompt_se_entienden():
    pregunta = "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"
    prompt = construir_prompt(pregunta, recuperar(pregunta))
    assert "85 %" in prompt


def test_el_modelo_recibe_el_contexto_recuperado():
    espia = ModeloEspia()
    ejecutar("¿Cuál es la escala de calificaciones y nota mínima de aprobación?", modelo=espia)
    assert len(espia.prompts) == 1
    assert "4.0" in espia.prompts[0]


def test_cadena_completa_con_el_modelo_simulado():
    texto, fuentes = ejecutar("¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?")
    assert "85 %" in texto
    assert "[1]" in texto
    assert fuentes == ["reglamento_asistencia.md"]
