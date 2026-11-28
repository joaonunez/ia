"""Pruebas parciales de detección mecánica de alucinaciones (U3.5 · Bloque 43)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import registrar_alucinaciones  # noqa: E402
from dobles import ModeloAlucinador  # noqa: E402
from servicio import cadena, fundamentacion  # noqa: E402


def test_respuesta_respaldada_no_reporta_problemas():
    frags = [
        {
            "fuente": "reglamento_asistencia.md",
            "texto": "El porcentaje mínimo de asistencia para promoción escolar es del 85 %.",
        }
    ]
    problemas = fundamentacion.problemas_de_respaldo(
        "El porcentaje mínimo de asistencia es 85 % según reglamento_asistencia.md [1].",
        frags,
        cadena.SIN_INFORMACION,
    )
    assert problemas == []


def test_detecta_cifra_inventada_ignorando_citas_y_archivos():
    frags = [
        {
            "fuente": "reglamento_asistencia.md",
            "texto": "El porcentaje mínimo de asistencia es del 85 %.",
        }
    ]
    problemas = fundamentacion.problemas_de_respaldo(
        "El mínimo es 92 % [1].",
        frags,
        cadena.SIN_INFORMACION,
    )
    assert ("cifra_inventada", "92") in problemas


def test_detecta_fuente_inventada():
    frags = [
        {
            "fuente": "reglamento_asistencia.md",
            "texto": "El porcentaje mínimo de asistencia es del 85 %.",
        }
    ]
    problemas = fundamentacion.problemas_de_respaldo(
        "Según manual_secreto_2099.pdf el mínimo es 85 %.",
        frags,
        cadena.SIN_INFORMACION,
    )
    assert ("fuente_inventada", "manual_secreto_2099.pdf") in problemas


def test_detecta_respuesta_sin_respaldo():
    problemas = fundamentacion.problemas_de_respaldo(
        "El director se llama Pedro.",
        [],
        cadena.SIN_INFORMACION,
    )
    assert any(codigo == "sin_respaldo" for codigo, _ in problemas)


def test_cadena_contiene_modelo_alucinador():
    texto, fuentes = cadena.ejecutar(
        "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?",
        ModeloAlucinador("El mínimo de asistencia es 99 % según decreto_falso.pdf."),
    )
    assert texto == cadena.SIN_INFORMACION
    assert fuentes == []


def test_sondas_de_alucinacion_cumplen_contrato():
    resultados = registrar_alucinaciones.evaluar_sondas()
    mapa = {r["id"]: r["estado"] for r in resultados}
    assert mapa["H-01"] == "PASA"
    assert mapa["H-02"] == "PASA"
    assert mapa["H-03"] == "PASA"
    assert mapa["H-04"] == "LIMITE"
    assert mapa["H-05"] == "LIMITE"
