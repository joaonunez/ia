"""Lectura aislada de configuración desde variables de entorno (U3.4 · Bloque 39)."""
from __future__ import annotations

import os


class ConfiguracionIncompleta(RuntimeError):
    """Falta una variable de entorno obligatoria para ejecutar el servicio."""


def entorno() -> str:
    """Devuelve el entorno configurado ('desarrollo' por omisión)."""
    valor = os.getenv("ENTORNO", "").strip()
    return valor or "desarrollo"


def modelo_configurado() -> bool:
    """Indica si existe una clave no vacía para el proveedor de modelo."""
    clave = (os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY") or "").strip()
    return bool(clave)


def clave_modelo() -> str:
    """Devuelve la clave del proveedor o falla nombrando la variable (nunca el valor)."""
    clave = (os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY") or "").strip()
    if not clave:
        raise ConfiguracionIncompleta(
            "Falta definir GEMINI_API_KEY (o API_KEY) en el entorno."
        )
    return clave


def modelo_pedido() -> str:
    """Qué modelo se solicita: 'simulado' (por omisión) o 'real'."""
    return os.getenv("MODELO", "simulado").strip().lower() or "simulado"


def respaldo_permitido() -> bool:
    """El respaldo solo se activa si se permite explícitamente con PERMITIR_RESPALDO=1."""
    return os.getenv("PERMITIR_RESPALDO", "0").strip() == "1"
