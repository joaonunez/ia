"""Guardias de contrato entre componentes de la cadena IA (U3.4 · Bloque 39)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError


class ContratoIncumplido(Exception):
    """Un componente entregó algo distinto del contrato prometido al siguiente."""


class Fragmento(BaseModel):
    """Contrato estricto de cada fragmento entregado por el recuperador."""

    model_config = ConfigDict(extra="forbid")

    fuente: str
    texto: str


def exigir(tipo: Any, valor: Any, componente: str) -> None:
    """Valida que `valor` cumpla `tipo` o falla nombrando al componente culpable.

    Nunca incluye el valor recibido en el mensaje de error (evita fuga de PII o secretos).
    """
    try:
        TypeAdapter(tipo).validate_python(valor)
    except ValidationError as error:
        problemas = "; ".join(
            f"{'.'.join(str(p) for p in err.get('loc', ())) or 'valor'}: {err.get('msg', 'valor inválido')}"
            for err in error.errors()
        )
        raise ContratoIncumplido(f"{componente} no cumple su contrato: {problemas}") from None
