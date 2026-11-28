"""Pruebas parciales de la rúbrica y verificador del Gate 3 (U3.7 · Bloque S2)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import rubrica_gate3 as r  # noqa: E402
import verificar_gate3 as g  # noqa: E402


def perfectos() -> dict[str, tuple[int, int]]:
    return {nombre: (5, 5) for nombre in g.FUENTES}


def test_pesos_suman_cien_y_fuentes_son_coherentes():
    assert sum(c["peso"] for c in r.CRITERIOS) == 100
    en_rubrica = {f for c in r.CRITERIOS for f in c["fuentes"]}
    assert en_rubrica == set(g.FUENTES.keys())


def test_cada_fuente_apunta_a_un_archivo_existente():
    for nombre, (orden, _) in g.FUENTES.items():
        if "-m" in orden:
            continue
        script = REPO_ROOT / orden[1]
        assert script.is_file(), f"Fuente {nombre} apunta a archivo inexistente: {script}"


def test_una_fuente_a_medias_resta_solo_su_parte():
    resultados = perfectos()
    resultados["readme"] = (4, 8)
    por_id = {c["id"]: p for c, p, _ in g.puntuar(resultados)}
    assert por_id["C7"] == 5 * (0.5 + 1) / 2
    assert por_id["C1"] == 10


def test_un_criterio_sin_evidencia_vale_cero():
    resultados = {f: v for f, v in perfectos().items() if f not in ("readme", "transferencia")}
    por_id = {c["id"]: p for c, p, _ in g.puntuar(resultados)}
    assert por_id["C7"] == 0


def test_un_secreto_expuesto_no_se_compensa_con_el_resto():
    resultados = perfectos()
    resultados["secretos"] = (4, 5)
    fallan = g.no_compensables_que_fallan(resultados)
    assert [nc["id"] for nc, _ in fallan] == ["NC-4"]
    assert g.decidir(95.0, fallan, [])[0] == "NO APRUEBA"


def test_sin_evidencia_de_un_no_compensable_tambien_falla():
    resultados = perfectos()
    del resultados["secretos"]
    fallan = g.no_compensables_que_fallan(resultados)
    assert "sin evidencia" in fallan[0][1]
    assert "NC-3" not in [nc["id"] for nc, _ in fallan]
    assert [i for i, _ in g.confirma_el_evaluador()] == ["NC-3", "NC-4"]


def test_escala_de_nota_cumple_exigencia_60_por_ciento():
    assert g.nota(0) == 1.0
    assert g.nota(60) == 4.0
    assert g.nota(80) == 5.5
    assert g.nota(100) == 7.0
