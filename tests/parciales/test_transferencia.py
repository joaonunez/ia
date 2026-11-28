"""Pruebas parciales de la prueba cruzada de transferencia (U3.6 · Bloque 45)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import registrar_transferencia  # noqa: E402
import verificar_transferencia  # noqa: E402


def test_huella_transferencia_es_determinista():
    h1 = registrar_transferencia.huella()
    h2 = registrar_transferencia.huella()
    assert h1 == h2 and len(h1) == 12


def test_verificar_transferencia_cumple_6_de_6():
    comprobaciones = verificar_transferencia.verificar()
    assert len(comprobaciones) == 6
    fallos = [(c, d) for c, ok, d in comprobaciones if not ok]
    assert not fallos, f"Reglas TRA fallidas: {fallos}"
