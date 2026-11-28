"""Pruebas unitarias e integración HTTP del servicio FastAPI (U3.2 · Bloque 35)."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from observability_security import trace_id_var
from servicio.main import app
from verificar_servicio import COMPROBACIONES, ejecutar

client = TestClient(app)


def test_health_endpoint_responds_ok_without_api_key():
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["estado"] == "ok"
    assert body["version"] == "0.2.0"


def test_openapi_docs_and_all_schema_fields_have_descriptions():
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert {"/health", "/ask", "/estudiantes/{nombre}"}.issubset(schema["paths"].keys())
    components = schema["components"]["schemas"]
    for model_name in (
        "Consulta",
        "Respuesta",
        "EstudianteResumen",
        "EstadoSalud",
        "CampoInvalido",
        "ErrorRespuesta",
    ):
        for field_name, meta in components[model_name]["properties"].items():
            assert "description" in meta, f"Falta description en {model_name}.{field_name}"


def test_verificar_servicio_passes_all_acceptance_criteria():
    assert ejecutar(COMPROBACIONES) is True


def test_ask_validates_invalid_payloads_with_422_and_wrong_method_with_405():
    # Falta campo obligatorio
    assert client.post("/ask", json={"texto": "hola"}).status_code == 422
    # Pregunta vacía o solo espacios
    assert client.post("/ask", json={"pregunta": "   "}).status_code == 422
    # Demasiado corta
    assert client.post("/ask", json={"pregunta": "ab"}).status_code == 422
    # Método incorrecto
    assert client.get("/ask").status_code == 405


def test_ask_does_not_leak_pii_in_logs_and_resets_trace_id(caplog):
    email = "ana.perez@example.com"
    question = f"¿Cuál es la asistencia mínima para promoción? Mi correo es {email}"

    with caplog.at_level(logging.INFO, logger="servicio.logica"):
        res = client.post("/ask", json={"pregunta": question})

    assert res.status_code == 200
    assert res.json()["trace_id"].startswith("trace-")
    assert trace_id_var.get() is None

    dump = " ".join(r.getMessage() + " " + str(r.__dict__) for r in caplog.records)
    assert email not in dump
    assert question not in dump


def test_estudiantes_endpoint_handles_accents_and_returns_404_when_unknown():
    res_ok = client.get("/estudiantes/sofia rojas")
    assert res_ok.status_code == 200
    assert res_ok.json()["nombre"] == "Sofía Rojas"
    assert res_ok.json()["simulado"] is True

    res_missing = client.get("/estudiantes/Estudiante Inexistente")
    assert res_missing.status_code == 404
    body_missing = res_missing.json()
    assert body_missing["codigo"] == "no_encontrado"
    assert "No se encontró" in body_missing["mensaje"]
