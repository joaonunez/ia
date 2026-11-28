"""Elección del modelo y componente de respaldo explícito (U3.4 · Bloque 41).

Reglas:
- Mismo contrato (`generar(prompt) -> str`) que la pieza real.
- Activación explícita: solo si `MODELO=real` y `PERMITIR_RESPALDO=1`.
- Sin permiso, falla a la vista con `ModeloNoDisponible` (HTTP 503).
- Visible en `GET /health` mediante `modelo_activo`.
"""
from __future__ import annotations

from servicio import config
from servicio.cadena import ModeloSimulado

# Pasa a True cuando el cliente real de Gemini esté integrado y verificado en producción.
CLIENTE_INTEGRADO = False


class ModeloNoDisponible(Exception):
    """El modelo solicitado no puede atender la petición en este momento."""


class ModeloReal:
    """Pieza real pendiente de activación controlada (ver docs/respaldos.md)."""

    nombre = "real"

    @staticmethod
    def motivo_no_disponible() -> str | None:
        """Devuelve el motivo por el cual no está disponible, o None si puede operar."""
        if not config.modelo_configurado():
            return "falta GEMINI_API_KEY"
        if not CLIENTE_INTEGRADO:
            return "el cliente de Gemini aún no está integrado en el servicio HTTP"
        return None

    def generar(self, prompt: str) -> str:
        motivo = self.motivo_no_disponible()
        if motivo:
            raise ModeloNoDisponible(motivo)
        raise ModeloNoDisponible("cliente real sin implementar")


class ModeloRespaldo(ModeloSimulado):
    """Reemplaza al modelo real cuando está incompleto y se autoriza explícitamente."""

    nombre = "respaldo"


def elegir_modelo() -> ModeloSimulado | ModeloRespaldo | ModeloReal:
    """Devuelve el modelo activo o lanza ModeloNoDisponible (HTTP 503)."""
    if config.modelo_pedido() != "real":
        return ModeloSimulado()
    motivo = ModeloReal.motivo_no_disponible()
    if motivo is None:
        return ModeloReal()
    if config.respaldo_permitido():
        return ModeloRespaldo()
    raise ModeloNoDisponible(motivo)
