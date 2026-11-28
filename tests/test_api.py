"""Suite parametrizada de casos válidos, inválidos y error 500 (U3.2 · Bloque 36)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from casos import CASOS, ejecutar_caso
from registrar_pruebas import verificar_cobertura
from servicio import logica
from servicio.main import app

cliente = TestClient(app, raise_server_exceptions=False)


def test_cobertura_minima_de_casos():
    assert verificar_cobertura(CASOS) == []


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_caso_http(caso):
    ok, estado, detalle = ejecutar_caso(cliente, caso)
    assert ok, f"{caso['id']} ({caso['descripcion']}): estado={estado}, detalle={detalle}"


def test_error_interno_500_devuelve_mensaje_generico_sin_filtrar_secretos(monkeypatch):
    def fallar_con_secreto(_pregunta: str):
        raise RuntimeError("Fallo con clave secreta sk-super-secreto-999")

    monkeypatch.setattr(logica, "responder_consulta", fallar_con_secreto)
    res = cliente.post("/ask", json={"pregunta": "¿Cuál es la asistencia mínima?"})

    assert res.status_code == 500
    cuerpo = res.json()
    assert cuerpo == {
        "codigo": "error_interno",
        "mensaje": "Ocurrió un error interno. Intenta de nuevo más tarde.",
        "campos": [],
    }
    assert "sk-super-secreto-999" not in res.text
    assert "Traceback" not in res.text
