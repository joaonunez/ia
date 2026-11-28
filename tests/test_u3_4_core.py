"""Pruebas intensivas del Core U3.4: 503 de respaldo, escenarios, registro y verificadores."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import registrar_ejecucion as reg_ej
import verificar_ejecucion as ver_ej
import verificar_registro as ver_reg
from servicio.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_health_y_ask_devuelven_503_cuando_modelo_real_no_tiene_respaldo(monkeypatch):
    monkeypatch.setenv("MODELO", "real")
    monkeypatch.setenv("PERMITIR_RESPALDO", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)

    r_health = client.get("/health")
    assert r_health.status_code == 503
    datos_h = r_health.json()
    assert datos_h["estado"] == "error"
    assert datos_h["modelo_activo"] == "ninguno"

    r_ask = client.post("/ask", json={"pregunta": "¿Cuál es el porcentaje mínimo de asistencia?"})
    assert r_ask.status_code == 503
    datos_a = r_ask.json()
    assert datos_a["codigo"] == "modelo_no_disponible"


def test_health_muestra_respaldo_cuando_se_permite_explicitamente(monkeypatch):
    monkeypatch.setenv("MODELO", "real")
    monkeypatch.setenv("PERMITIR_RESPALDO", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)

    r_health = client.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["modelo_activo"] == "respaldo"

    r_ask = client.post("/ask", json={"pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"})
    assert r_ask.status_code == 200
    assert "85 %" in r_ask.json()["respuesta"]


def test_verificar_ejecucion_valida_escenarios_y_bitacora():
    ok_esc, _ = ver_ej.escenarios_completos()
    ok_bit, _ = ver_ej.bitacora_completa(REPO_ROOT)
    assert ok_esc is True
    assert ok_bit is True


def test_registrar_ejecucion_conserva_zona_manual_y_detecta_secretos():
    previo = (
        "# Registro de ejecución\n\n"
        "<!-- AUTO:INICIO -->\nviejo\n<!-- AUTO:FIN -->\n\n"
        "## Qué se observó\nTexto manual conservado intacto."
    )
    nuevo = reg_ej.armar("nuevo bloque automatico", previo)
    assert "nuevo bloque automatico" in nuevo
    assert "viejo" not in nuevo
    assert "Texto manual conservado intacto." in nuevo

    assert reg_ej.con_forma_de_secreto("AIza" + "A" * 35) is True
    assert reg_ej.con_forma_de_secreto("registro limpio sin claves") is False


def test_verificar_registro_detecta_manual_incompleto_y_respaldo_no_declarado():
    incompleto = (
        "# Registro\n<!-- AUTO:INICIO -->\n| Modelo | respaldo | x |\n<!-- AUTO:FIN -->\n"
        "## Qué se observó\n[COMPLETAR]\n"
        "## Qué no se probó\nTexto sin mencionar el componente ni la palabra clave requerida.\n"
        "## Siguiente paso\nCorto.\n"
    )
    ok_man, _ = ver_reg.manual_completo(incompleto)
    ok_resp, _ = ver_reg.respaldos_declarados(incompleto)
    assert ok_man is False
    assert ok_resp is False
