"""Lector estructurado de la Ficha de Diseño Funcional (U3.1 · Bloque 34)."""
from __future__ import annotations

import re
from typing import Any

from verificar_ficha import RUTA, leer_secciones


def _extraer_horas(patron: str, texto: str) -> float | None:
    m = re.search(patron, texto, re.MULTILINE)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


def cargar(ruta: str = RUTA) -> dict[str, Any]:
    """Carga y parsea las cinco secciones de la Ficha de Diseño Funcional."""
    with open(ruta, encoding="utf-8") as archivo:
        texto = archivo.read()

    secciones = leer_secciones(texto)
    texto2 = secciones.get(2, ("", ""))[1]
    texto4 = secciones.get(4, ("", ""))[1]
    texto5 = secciones.get(5, ("", ""))[1]

    rf = dict(re.findall(r"(?m)^- (RF-\d{2}): (.+)$", texto2))
    rnf = dict(re.findall(r"(?m)^- (RNF-\d{2}): (.+)$", texto2))

    cajones: dict[str, list[str]] = {}
    for nombre in ("Imprescindible", "Deseable", "Fuera de alcance"):
        m = re.search(rf"(?m)^{nombre}:\s*(.*)$", texto2)
        cajones[nombre] = re.findall(r"RF-\d{2}", m.group(1)) if m else []

    criterios: list[dict[str, Any]] = []
    for cid, cubre_raw, desc in re.findall(
        r"(?m)^- (CA-\d{2}) \(([^)]+)\): (.+)$", texto4
    ):
        criterios.append(
            {
                "id": cid,
                "cubre": re.findall(r"R(?:N)?F-\d{2}", cubre_raw),
                "texto": desc.strip(),
            }
        )

    disponibles = _extraer_horas(r"^Horas disponibles:\s*([\d.,]+)\s*h", texto5)
    margen = _extraer_horas(r"^Margen de imprevistos:\s*([\d.,]+)\s*h", texto5)

    hitos: list[dict[str, Any]] = []
    for hid, horas_raw, desc, cubre_raw, ca_raw in re.findall(
        r"(?m)^- (H\d+) \(([\d.,]+)\s*h\):\s*(.+?)\.\s*Cubre:\s*(.+?)\.\s*Se comprueba con:\s*(.+?)\.?$",
        texto5,
    ):
        hitos.append(
            {
                "id": hid,
                "horas": float(horas_raw.replace(",", ".")),
                "descripcion": desc.strip(),
                "cubre": re.findall(r"R(?:N)?F-\d{2}", cubre_raw),
                "criterios": re.findall(r"CA-\d{2}", ca_raw),
            }
        )

    return {
        "rf": rf,
        "rnf": rnf,
        "cajones": cajones,
        "texto4": texto4,
        "texto5": texto5,
        "criterios": criterios,
        "disponibles": disponibles,
        "margen": margen,
        "hitos": hitos,
    }
