"""Pruebas unitarias de la Ficha de Diseño Funcional y verificadores (U3.1 · Bloques 33 y 34)."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ficha_datos import cargar
from verificar_ficha import verificar
from verificar_ficha_completa import (
    verificar_criterios,
    verificar_pendientes,
    verificar_plan,
    verificar_revision,
)


def test_real_design_spec_passes_all_verifiers_without_errors_or_warnings(monkeypatch):
    monkeypatch.chdir(REPO_ROOT)

    ficha_text = (REPO_ROOT / "docs" / "ficha_diseno_funcional.md").read_text(encoding="utf-8")
    errores, avisos = verificar(ficha_text)
    assert errores == []
    assert avisos == []

    ficha = cargar()
    assert verificar_pendientes(ficha) == []

    errores_ca, avisos_ca = verificar_criterios(ficha)
    assert errores_ca == []
    assert avisos_ca == []

    assert verificar_plan(ficha) == []
    assert verificar_revision() == []


def test_verificar_ficha_detects_solution_word_and_missing_numbers():
    bad_spec = """# Ficha de Diseño Funcional

## 1. Problema de negocio
Necesito un chatbot para responder rápido.

## 2. Requerimientos y alcance (MVP)
### Requerimientos funcionales
- RF-01: Uno.
- RF-02: Dos.
- RF-03: Tres.
### Requerimientos no funcionales
- RNF-01: El sistema es rápido.
- RNF-02: El sistema es seguro.
### Alcance
Imprescindible: RF-01, RF-02, RF-03
Deseable:
Fuera de alcance:

## 3. Arquitectura de la solución
Sin diagrama.

## 4. Criterios de aceptación
[PENDIENTE]

## 5. Plan de construcción por hitos
[PENDIENTE]
"""
    errores, avisos = verificar(bad_spec)
    assert any("chatbot" in a for a in avisos)
    assert any("RNF-01" in e for e in errores)
    assert any("diagrama" in e for e in errores)


def test_verificar_revision_enforces_two_space_indent_and_tilde(tmp_path):
    bad_rev = tmp_path / "revision.md"
    bad_rev.write_text(
        "# Revisión\n"
        "- Hallazgo 1: falta algo.\n"
        " Decisión: aceptado. Cambio.\n"
        "- Hallazgo 2: otra cosa.\n"
        "  Decision: rechazado. Sin tilde.\n",
        encoding="utf-8",
    )
    errores = verificar_revision(str(bad_rev))
    assert any("Decisión:" in e for e in errores)
