"""Pruebas parciales del ensayo de demo `ensayo_demo.py` (U3.7 · Bloque S2)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import ensayo_demo as e  # noqa: E402


def test_evaluar_paso_valido_y_errores_controlados():
    paso = e.PASOS[0]
    ok, _ = e.evaluar(paso, 200, '{"estado":"ok","modelo_activo":"simulado"}', 0.05)
    assert ok

    ok_estado, _ = e.evaluar(paso, 500, '{"modelo_activo":"simulado"}', 0.05)
    assert not ok_estado

    ok_texto, _ = e.evaluar(paso, 200, '{"estado":"ok"}', 0.05)
    assert not ok_texto

    ok_lento, _ = e.evaluar(paso, 200, '{"modelo_activo":"simulado"}', 3.5)
    assert not ok_lento


def test_si_el_servicio_no_arranca_ningun_paso_pasa_en_vacio():
    resultados, _, _ = e.ensayar({"con_modelo": None, "sin_modelo": None})
    assert len(resultados) == len(e.PASOS)
    assert not any(ok for _, _, ok, _ in resultados)


def test_hablar_mas_de_la_cuenta_no_cabe():
    ok_largo, _ = e.tiempo(habla=70.0, servicio=0.0)
    assert not ok_largo
    ok_corto, _ = e.tiempo(habla=40.0, servicio=0.0)
    assert ok_corto


def test_tiempo_actual_de_los_7_pasos_cabe_en_120_segundos():
    habla = sum(e.segundos_de_habla(p) for p in e.PASOS)
    ok, detalle = e.tiempo(habla, 0.2)
    assert ok, detalle
