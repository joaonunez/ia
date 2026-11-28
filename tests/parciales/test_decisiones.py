"""Pruebas parciales de decisiones de arquitectura y limitaciones (Core U3.6 · Bloque 45)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import verificar_decisiones  # noqa: E402


def test_verificar_decisiones_cumple_7_de_7():
    comprobaciones = verificar_decisiones.verificar()
    assert len(comprobaciones) == 7
    fallos = [(c, d) for c, ok, d in comprobaciones if not ok]
    assert not fallos, f"Reglas DEC fallidas: {fallos}"
