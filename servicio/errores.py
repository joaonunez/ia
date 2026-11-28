"""Formato único de error y manejadores globales del servicio FastAPI (U3.2 · Bloque 36)."""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from servicio.contratos import ContratoIncumplido
from servicio.respaldo import ModeloNoDisponible

logger = logging.getLogger("servicio.errores")

CODIGOS: dict[int, str] = {
    404: "no_encontrado",
    405: "metodo_no_permitido",
}


def construir_error(
    estado: int,
    codigo: str,
    mensaje: str,
    campos: list[dict[str, str]] | None = None,
) -> JSONResponse:
    """Construye una respuesta JSON de error con contrato uniforme."""
    return JSONResponse(
        status_code=estado,
        content={
            "codigo": codigo,
            "mensaje": mensaje,
            "campos": campos or [],
        },
    )


async def manejar_entrada_invalida(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Devuelve 422 uniforme sin reenviar el input crudo del cliente (privacidad)."""
    campos = [
        {
            "campo": ".".join(str(parte) for parte in err.get("loc", ())),
            "motivo": str(err.get("msg", "Valor inválido")),
        }
        for err in exc.errors()
    ]
    return construir_error(
        422,
        "entrada_invalida",
        "Los datos enviados no cumplen el formato esperado.",
        campos,
    )


async def manejar_error_http(
    _request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Unifica errores HTTP de FastAPI/Starlette (404, 405, etc.)."""
    codigo = CODIGOS.get(exc.status_code, f"http_{exc.status_code}")
    if exc.status_code == 404 and exc.detail == "Not Found":
        mensaje = "El recurso solicitado no existe."
    elif exc.status_code == 405 and exc.detail == "Method Not Allowed":
        mensaje = "El método HTTP no está permitido para esta ruta."
    else:
        mensaje = str(exc.detail) if exc.detail else "Error en la solicitud."
    return construir_error(exc.status_code, codigo, mensaje)


async def manejar_error_interno(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Devuelve 500 genérico sin filtrar trazas, rutas ni secretos al cliente."""
    detalle = str(exc) if isinstance(exc, ContratoIncumplido) else type(exc).__name__
    logger.error(
        "error interno en %s %s: %s",
        request.method,
        request.url.path,
        detalle,
    )
    return construir_error(
        500,
        "error_interno",
        "Ocurrió un error interno. Intenta de nuevo más tarde.",
    )


async def manejar_modelo_no_disponible(
    _request: Request,
    exc: ModeloNoDisponible,
) -> JSONResponse:
    """Devuelve 503 explícito cuando el modelo real no está disponible sin respaldo."""
    return construir_error(
        503,
        "modelo_no_disponible",
        f"El modelo no está disponible: {exc}.",
    )


def registrar(app: FastAPI) -> None:
    """Registra los manejadores globales de error en la aplicación FastAPI."""
    app.add_exception_handler(ModeloNoDisponible, manejar_modelo_no_disponible)
    app.add_exception_handler(RequestValidationError, manejar_entrada_invalida)
    app.add_exception_handler(StarletteHTTPException, manejar_error_http)
    app.add_exception_handler(Exception, manejar_error_interno)
