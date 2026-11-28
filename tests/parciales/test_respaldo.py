"""Pruebas parciales del selector de modelo y componente de respaldo (U3.4 · Bloque 41)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio import respaldo
from servicio.cadena import ModeloSimulado, SIN_INFORMACION


def test_por_omision_elige_modelo_simulado(monkeypatch):
    monkeypatch.delenv("MODELO", raising=False)
    monkeypatch.delenv("PERMITIR_RESPALDO", raising=False)
    modelo = respaldo.elegir_modelo()
    assert isinstance(modelo, ModeloSimulado)
    assert modelo.nombre == "simulado"


def test_modelo_real_sin_permiso_de_respaldo_falla_a_la_vista(monkeypatch):
    monkeypatch.setenv("MODELO", "real")
    monkeypatch.setenv("PERMITIR_RESPALDO", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(respaldo.ModeloNoDisponible) as error:
        respaldo.elegir_modelo()
    assert "GEMINI_API_KEY" in str(error.value)


def test_modelo_real_con_permiso_de_respaldo_elige_respaldo(monkeypatch):
    monkeypatch.setenv("MODELO", "real")
    monkeypatch.setenv("PERMITIR_RESPALDO", "1")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    modelo = respaldo.elegir_modelo()
    assert isinstance(modelo, respaldo.ModeloRespaldo)
    assert modelo.nombre == "respaldo"


def test_respaldo_no_se_activa_si_se_pidio_simulado(monkeypatch):
    monkeypatch.setenv("MODELO", "simulado")
    monkeypatch.setenv("PERMITIR_RESPALDO", "1")
    assert respaldo.elegir_modelo().nombre == "simulado"


def test_con_clave_pero_sin_cliente_integrado_falla_sin_respaldo(monkeypatch):
    monkeypatch.setenv("MODELO", "real")
    monkeypatch.setenv("PERMITIR_RESPALDO", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(respaldo, "CLIENTE_INTEGRADO", False)
    with pytest.raises(respaldo.ModeloNoDisponible) as error:
        respaldo.elegir_modelo()
    assert "integrado" in str(error.value)


def test_con_clave_y_cliente_integrado_elige_modelo_real(monkeypatch):
    monkeypatch.setenv("MODELO", "real")
    monkeypatch.setenv("PERMITIR_RESPALDO", "0")
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    monkeypatch.setattr(respaldo, "CLIENTE_INTEGRADO", True)
    assert respaldo.elegir_modelo().nombre == "real"


@pytest.mark.parametrize("clase", [ModeloSimulado, respaldo.ModeloRespaldo, respaldo.ModeloReal])
def test_contrato_todos_los_modelos_cumplen_generar(clase):
    if clase is respaldo.ModeloReal:
        motivo = respaldo.ModeloReal.motivo_no_disponible()
        if motivo:
            pytest.skip(f"modelo real no disponible: {motivo}")
    modelo = clase()
    prompt_con = "Responde usando todo el contexto.\nContexto:\n- Asistencia 85 %.\nPregunta: P"
    prompt_sin = "Responde usando todo el contexto.\nContexto:\n\nPregunta: P"
    salida_con = modelo.generar(prompt_con)
    salida_sin = modelo.generar(prompt_sin)
    assert isinstance(salida_con, str) and "85 %" in salida_con
    assert salida_sin == SIN_INFORMACION
