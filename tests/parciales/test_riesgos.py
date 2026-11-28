"""Pruebas parciales de la Matriz de Riesgos y reglas RIE-1..RIE-6 (Core U3.5 · Bloque 43)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import riesgos  # noqa: E402
import verificar_riesgos  # noqa: E402


def test_categorias_y_huella_riesgos():
    assert riesgos.categoria(15) == "CRITICO"
    assert riesgos.categoria(9) == "ALTO"
    assert riesgos.categoria(4) == "MEDIO"
    assert riesgos.categoria(3) == "BAJO"
    h = riesgos.huella(riesgos.RIESGOS)
    assert len(h) == 12


def test_verificar_riesgos_cumple_6_de_6():
    comprobaciones = verificar_riesgos.verificar()
    assert len(comprobaciones) == 6
    fallos = [(c, d) for c, ok, d in comprobaciones if not ok]
    assert not fallos, f"Reglas RIE fallidas: {fallos}"
