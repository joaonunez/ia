"""Diagnóstico paso a paso de la cadena IA sin necesidad de Docker (U3.4 · Bloque 39).

Uso:
    python diagnostico.py
    python diagnostico.py "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"
"""
from __future__ import annotations

import sys
from typing import Any, Callable

from servicio import cadena


def forma(valor: Any) -> str:
    """Resume el tipo y claves de una salida sin volcar contenido sensible completo."""
    if isinstance(valor, list):
        claves = sorted({k for elem in valor if isinstance(elem, dict) for k in elem})
        return f"lista de {len(valor)} elemento(s), claves {claves}"
    return f"{type(valor).__name__}: {str(valor)[:55]!r}"


def paso(nombre: str, funcion: Callable[..., Any], *args: Any) -> Any:
    try:
        resultado = funcion(*args)
    except Exception as error:
        print(f"FALLA {nombre} -> {type(error).__name__}: {error}")
        raise SystemExit(1)
    print(f"ok {nombre} -> {forma(resultado)}")
    return resultado


def main(pregunta: str) -> None:
    modelo = cadena.ModeloSimulado()
    fragmentos = paso("recuperar", cadena.recuperar, pregunta)
    prompt = paso("construir_prompt", cadena.construir_prompt, pregunta, fragmentos)
    texto = paso("generar", modelo.generar, prompt)
    paso("empaquetar", cadena.empaquetar, texto, fragmentos)


if __name__ == "__main__":
    consulta = " ".join(sys.argv[1:]) or "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"
    main(consulta)
