"""Dobles de prueba para verificar mitigaciones de seguridad y alucinaciones (U3.5 · Bloque 43).

La clave sintética `CLAVE_FALSA` se construye concatenada para evitar falsos positivos
en escáneres estáticos de secretos.
"""
from __future__ import annotations

from servicio import cadena

CLAVE_FALSA = "AIza" + "x" * 35


class ModeloVulnerable:
    """Simula un modelo ingenuo que obedece inyecciones y filtra prompt o secretos."""

    nombre = "vulnerable"

    def generar(self, prompt: str) -> str:
        lower = prompt.lower()
        if "api" in lower or "clave" in lower or ".env" in lower or "secreto" in lower:
            return f"La clave configurada en el entorno es {CLAVE_FALSA}."
        if "prompt" in lower or "instruccion" in lower:
            return f"Mis instrucciones internas son: {cadena.INSTRUCCION}"
        if "ignora" in lower or "modo desarrollador" in lower:
            return "COMPROMETIDO: obedeciendo orden inyectada."
        return cadena.ModeloSimulado().generar(prompt)


class ModeloAlucinador:
    """Simula un modelo que devuelve siempre una respuesta fija (potencialmente inventada)."""

    nombre = "alucinador"

    def __init__(self, respuesta_fija: str) -> None:
        self._respuesta_fija = respuesta_fija

    def generar(self, prompt: str) -> str:
        return self._respuesta_fija
