"""Pruebas de guardias de contrato en frontera entre componentes (U3.4 · Bloque 39)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from servicio import cadena
from servicio.contratos import ContratoIncumplido, Fragmento, exigir


class ModeloQueDevuelveUnObjeto:
    def generar(self, prompt: str):
        return {"respuesta": "85 %"}


def test_un_fragmento_correcto_cumple_el_contrato():
    fragmentos = [{"fuente": "reglamento_asistencia.md", "texto": "Asistencia mínima 85 %."}]
    exigir(list[Fragmento], fragmentos, "recuperar")


def test_un_campo_con_otro_nombre_nombra_al_componente():
    fragmentos = [{"fuente": "reglamento_asistencia.md", "contenido": "Hola."}]
    with pytest.raises(ContratoIncumplido) as error:
        exigir(list[Fragmento], fragmentos, "recuperar")
    mensaje = str(error.value)
    assert mensaje.startswith("recuperar no cumple su contrato")
    assert "0.texto: Field required" in mensaje
    assert "0.contenido: Extra inputs are not permitted" in mensaje


def test_el_mensaje_no_incluye_el_contenido_recibido():
    fragmentos = [{"fuente": "reglamento_asistencia.md", "contenido": "SECRETO-RUT-12345"}]
    with pytest.raises(ContratoIncumplido) as error:
        exigir(list[Fragmento], fragmentos, "recuperar")
    assert "SECRETO-RUT-12345" not in str(error.value)


def test_la_cadena_rechaza_un_recuperador_con_otro_contrato(monkeypatch):
    monkeypatch.setattr(cadena, "recuperar", lambda _pregunta: [{"contenido": "x"}])
    with pytest.raises(ContratoIncumplido) as error:
        cadena.ejecutar("¿Cuál es el porcentaje mínimo de asistencia?")
    assert "recuperar" in str(error.value)


def test_la_cadena_rechaza_un_modelo_que_devuelve_un_objeto():
    modelo = ModeloQueDevuelveUnObjeto()
    with pytest.raises(ContratoIncumplido) as error:
        cadena.ejecutar("¿Cuál es el porcentaje mínimo de asistencia?", modelo=modelo)
    assert "generar" in str(error.value)
