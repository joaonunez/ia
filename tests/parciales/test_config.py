"""Pruebas parciales aisladas de `servicio/config.py` (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio import config


def test_entorno_por_omision_es_desarrollo(monkeypatch):
    monkeypatch.delenv("ENTORNO", raising=False)
    assert config.entorno() == "desarrollo"


def test_entorno_toma_el_valor_de_la_variable(monkeypatch):
    monkeypatch.setenv("ENTORNO", "produccion")
    assert config.entorno() == "produccion"


def test_sin_clave_el_modelo_no_esta_configurado(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    assert config.modelo_configurado() is False


def test_con_clave_el_modelo_esta_configurado(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    assert config.modelo_configurado() is True


def test_clave_vacia_cuenta_como_ausente(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("API_KEY", "   ")
    assert config.modelo_configurado() is False


def test_sin_clave_pedirla_falla_nombrando_la_variable(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(config.ConfiguracionIncompleta) as error:
        config.clave_modelo()
    assert "GEMINI_API_KEY" in str(error.value)


def test_contrato_la_clave_es_un_texto_y_no_se_filtra_al_error(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "clave-de-prueba")
    assert isinstance(config.clave_modelo(), str)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("API_KEY", raising=False)
    with pytest.raises(config.ConfiguracionIncompleta) as error:
        config.clave_modelo()
    assert "clave-de-prueba" not in str(error.value)
