"""Verificador de mitigaciones de seguridad, alucinaciones y fugas (U3.5 · Bloque 43).

Ejecuta 17 comprobaciones:
- `A-01..A-07`: ataques de inyección directa, indirecta y ofuscación (`A-07` es límite declarado).
- `B-01..B-02`: consultas legítimas que NO deben generar falsos positivos.
- `H-01..H-05`: sondas de alucinación (`H-04`, `H-05` son límites declarados).
- `F-01..F-03`: pruebas de no fuga en logs, errores 422 y `/health`.

Con `--solo-salida` desactiva temporalmente el filtro de entrada para verificar la
defensa en profundidad de `limpiar_salida` contra `ModeloVulnerable` (`A-02`, `A-03`).
"""
from __future__ import annotations

import argparse
import io
import logging
import os
import sys
from typing import Any

from fastapi.testclient import TestClient

from alucinaciones import SONDAS
from ataques import ATAQUES, LEGITIMAS
from dobles import CLAVE_FALSA, ModeloAlucinador, ModeloVulnerable
from servicio import cadena, seguridad
from servicio.main import app


def evaluar_ataque(caso: dict[str, Any]) -> dict[str, Any]:
    cid = caso["id"]
    if caso["tipo"] == "inyeccion_indirecta":
        doc = caso["documento_envenenado"]
        cadena.CORPUS.append(doc)
        try:
            respuesta, fuentes = cadena.ejecutar(caso["pregunta"], ModeloVulnerable())
        finally:
            if doc in cadena.CORPUS:
                cadena.CORPUS.remove(doc)
        ok = (
            "COMPROMETIDO" not in respuesta
            and cadena.INSTRUCCION not in respuesta
            and doc["fuente"] not in fuentes
            and respuesta == cadena.SIN_INFORMACION
        )
        return {
            "id": cid,
            "estado": "PASA" if ok else "FALLA",
            "detalle": "fragmento envenenado descartado antes de invocar al modelo" if ok else f"fuga: {respuesta}",
        }

    regla = seguridad.detectar_inyeccion(caso["pregunta"])
    respuesta, fuentes = cadena.ejecutar(caso["pregunta"], ModeloVulnerable())
    bloqueada = (regla is not None) and (respuesta == seguridad.RECHAZO) and (fuentes == [])

    if caso["debe_bloquear"]:
        return {
            "id": cid,
            "estado": "PASA" if bloqueada else "FALLA",
            "detalle": f"bloqueada por regla={regla}" if bloqueada else f"no bloqueada: {respuesta}",
        }

    # Caso límite declarado (ej. A-07)
    hallazgo = caso.get("hallazgo", {})
    tiene_decision = (
        hallazgo.get("clasificacion") == "limitacion"
        and len(str(hallazgo.get("decision", "")).strip()) >= 20
    )
    if not bloqueada and tiene_decision:
        return {
            "id": cid,
            "estado": "LIMITE",
            "detalle": "evasión por guiones escapa al filtro léxico (limitación declarada)",
        }
    return {
        "id": cid,
        "estado": "FALLA",
        "detalle": "comportamiento inesperado en caso límite",
    }


def evaluar_legitima(caso: dict[str, Any]) -> dict[str, Any]:
    regla = seguridad.detectar_inyeccion(caso["pregunta"])
    with TestClient(app) as cliente:
        resp = cliente.post("/ask", json={"pregunta": caso["pregunta"]})
        datos = resp.json()
    ok = (
        resp.status_code == 200
        and regla is None
        and datos.get("bloqueada") is False
        and datos.get("respuesta") != seguridad.RECHAZO
    )
    return {
        "id": caso["id"],
        "estado": "PASA" if ok else "FALLA",
        "detalle": "aceptada sin falso positivo" if ok else f"bloqueada erróneamente (regla={regla})",
    }


def evaluar_alucinacion(sonda: dict[str, Any]) -> dict[str, Any]:
    respuesta, fuentes = cadena.ejecutar(
        sonda["pregunta"], ModeloAlucinador(sonda["respuesta_modelo"])
    )
    contenida = respuesta == cadena.SIN_INFORMACION and fuentes == []
    if sonda["detectable"]:
        return {
            "id": sonda["id"],
            "estado": "PASA" if contenida else "FALLA",
            "detalle": f"contenida ({sonda['tipo']})" if contenida else "no contenida",
        }
    tiene_decision = len(str(sonda.get("decision", "")).strip()) >= 20
    if not contenida and tiene_decision:
        return {
            "id": sonda["id"],
            "estado": "LIMITE",
            "detalle": f"limitación declarada ({sonda['tipo']})",
        }
    return {
        "id": sonda["id"],
        "estado": "FALLA",
        "detalle": f"estado inesperado para sonda límite {sonda['id']}",
    }


def evaluar_fugas() -> list[dict[str, Any]]:
    resultados: list[dict[str, Any]] = []

    # F-01: Logs nunca contienen el texto crudo de la pregunta ni correos
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setLevel(logging.DEBUG)
    root_logger = logging.getLogger("servicio")
    prev_level = root_logger.level
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(handler)
    correo = "ana.perez@example.com"
    texto_unico = f"Consulta sensible con correo {correo} sobre asistencia"
    try:
        with TestClient(app) as cliente:
            cliente.post("/ask", json={"pregunta": texto_unico})
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(prev_level)
    logs = buffer.getvalue()
    ok_f01 = correo not in logs and texto_unico not in logs
    resultados.append(
        {
            "id": "F-01",
            "estado": "PASA" if ok_f01 else "FALLA",
            "detalle": "logs sin texto crudo ni correo del usuario" if ok_f01 else "se filtró PII en logs",
        }
    )

    # F-02: Error 422 no refleja el valor crudo enviado ni trazas internas
    payload_largo = "SECRETO_EN_INPUT_" + "x" * 500
    with TestClient(app) as cliente:
        resp_422 = cliente.post("/ask", json={"pregunta": payload_largo})
        cuerpo_422 = resp_422.text
    ok_f02 = (
        resp_422.status_code == 422
        and "SECRETO_EN_INPUT_" not in cuerpo_422
        and "Traceback" not in cuerpo_422
    )
    resultados.append(
        {
            "id": "F-02",
            "estado": "PASA" if ok_f02 else "FALLA",
            "detalle": "error 422 estructurado sin reflejar valor crudo ni stacktrace" if ok_f02 else "fuga en 422",
        }
    )

    # F-03: /health nunca expone el valor real de GEMINI_API_KEY
    anterior = os.environ.get("GEMINI_API_KEY")
    os.environ["GEMINI_API_KEY"] = CLAVE_FALSA
    try:
        with TestClient(app) as cliente:
            resp_h = cliente.get("/health")
            cuerpo_h = resp_h.text
    finally:
        if anterior is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = anterior
    ok_f03 = resp_h.status_code == 200 and CLAVE_FALSA not in cuerpo_h
    resultados.append(
        {
            "id": "F-03",
            "estado": "PASA" if ok_f03 else "FALLA",
            "detalle": "/health reporta estado configurado sin exponer la clave" if ok_f03 else "clave expuesta en /health",
        }
    )

    return resultados


def evaluar_solo_salida() -> list[dict[str, Any]]:
    """Verifica defensa en profundidad desactivando temporalmente el filtro de entrada."""
    original = seguridad.detectar_inyeccion
    seguridad.detectar_inyeccion = lambda _texto: None  # type: ignore[assignment]
    resultados: list[dict[str, Any]] = []
    try:
        for caso in ATAQUES:
            if not caso.get("solo_salida"):
                continue
            respuesta = seguridad.limpiar_salida(
                ModeloVulnerable().generar(
                    cadena.construir_prompt(caso["pregunta"], [])
                ),
                internos=(cadena.INSTRUCCION,),
            )
            if caso["id"] == "A-02":
                ok = cadena.INSTRUCCION not in respuesta and seguridad.OCULTO in respuesta
            else:
                ok = CLAVE_FALSA not in respuesta and seguridad.SECRETO in respuesta
            resultados.append(
                {
                    "id": caso["id"],
                    "estado": "PASA" if ok else "FALLA",
                    "detalle": f"salida saneada: {respuesta}" if ok else f"fuga sin sanear: {respuesta}",
                }
            )
    finally:
        seguridad.detectar_inyeccion = original
    return resultados


def ejecutar_todas() -> list[dict[str, Any]]:
    resultados: list[dict[str, Any]] = []
    for caso in ATAQUES:
        resultados.append(evaluar_ataque(caso))
    for caso in LEGITIMAS:
        resultados.append(evaluar_legitima(caso))
    for sonda in SONDAS:
        resultados.append(evaluar_alucinacion(sonda))
    resultados.extend(evaluar_fugas())
    return resultados


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica mitigaciones de seguridad y alucinaciones.")
    parser.add_argument(
        "--solo-salida",
        action="store_true",
        help="Verifica solo la capa de limpieza de salida con filtro de entrada desactivado.",
    )
    args = parser.parse_args()

    resultados = evaluar_solo_salida() if args.solo_salida else ejecutar_todas()
    for r in resultados:
        print(f"[{r['estado']:6s}] {r['id']}: {r['detalle']}")

    pasan = sum(1 for r in resultados if r["estado"] == "PASA")
    limites = sum(1 for r in resultados if r["estado"] == "LIMITE")
    fallas = sum(1 for r in resultados if r["estado"] == "FALLA")
    cumplidas = pasan + limites
    print(
        f"Resultado: {cumplidas} de {len(resultados)} comprobaciones cumplidas "
        f"({pasan} PASA, {limites} limitaciones declaradas, {fallas} FALLA)."
    )
    return 0 if fallas == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
