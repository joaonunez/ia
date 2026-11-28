"""Pruebas unitarias de Docker, Compose, secretos, interfaz y entrega U3.3 (Bloques 37-38)."""
from __future__ import annotations

import sys
from pathlib import Path

from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import buscar_secretos
from interfaz.main import app as interfaz_app
from verificar_dockerfile import comprobar_dockerfile
import verificar_entrega


def test_dockerfile_api_e_interfaz_cumplen_todas_las_reglas():
    for ruta in (REPO_ROOT / "Dockerfile", REPO_ROOT / "interfaz" / "Dockerfile"):
        resultados = comprobar_dockerfile(ruta)
        fallos = [(regla, detalle) for regla, ok, detalle in resultados if not ok]
        assert fallos == [], f"Reglas incumplidas en {ruta}: {fallos}"


def test_buscar_secretos_pasa_las_cinco_comprobaciones():
    assert buscar_secretos.ejecutar(REPO_ROOT) is True


def test_verificar_entrega_pasa_las_siete_comprobaciones():
    assert verificar_entrega.ejecutar(REPO_ROOT) is True


def test_interfaz_web_responde_html_y_salud():
    cliente = TestClient(interfaz_app)
    r_home = cliente.get("/")
    assert r_home.status_code == 200
    assert "Asistente Académico IA" in r_home.text

    r_health = cliente.get("/health")
    assert r_health.status_code == 200
    assert r_health.json()["estado"] == "ok"
