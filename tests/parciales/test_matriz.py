"""Pruebas parciales de la Matriz de Pruebas y reglas MAT-1..MAT-6 (U3.5 · Bloque 42)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import ejecutar_matriz  # noqa: E402
import matriz_modelo  # noqa: E402
import matriz_pruebas  # noqa: E402
import verificar_matriz  # noqa: E402


def test_huella_es_determinista_y_de_12_hex():
    h1 = ejecutar_matriz.huella(matriz_pruebas.MATRIZ)
    h2 = ejecutar_matriz.huella(matriz_pruebas.MATRIZ)
    assert h1 == h2
    assert len(h1) == 12
    assert all(c in "0123456789abcdef" for c in h1)


def test_matriz_pruebas_pasa_todos_los_escenarios():
    resultados = ejecutar_matriz.ejecutar(matriz_pruebas.MATRIZ)
    assert len(resultados) >= 5
    assert all(r["resultado"] == "PASA" for r in resultados)
    assert all(r["estado"] < 500 for r in resultados)


def test_matriz_modelo_registra_limitacion_mp08():
    resultados = ejecutar_matriz.ejecutar(matriz_modelo.MATRIZ)
    mapa = {r["id"]: r for r in resultados}
    assert mapa["MP-07"]["resultado"] == "PASA"
    assert mapa["MP-08"]["resultado"] == "FALLA"
    assert mapa["MP-08"]["hallazgo"]["clasificacion"] == "limitacion"
    assert len(mapa["MP-08"]["hallazgo"]["decision"]) >= 20


def test_verificar_matriz_cumple_6_de_6():
    comprobaciones = verificar_matriz.verificar("matriz_pruebas")
    assert len(comprobaciones) == 6
    fallos = [(c, d) for c, ok, d in comprobaciones if not ok]
    assert not fallos, f"Reglas fallidas: {fallos}"
