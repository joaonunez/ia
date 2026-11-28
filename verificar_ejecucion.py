"""Verifica la ejecución end-to-end y su bitácora de ajustes (U3.4 · Bloques 40-41)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import httpx2

import ejecutar_escenarios as ee
from escenarios import ESCENARIOS

BITACORA = Path("docs/bitacora_ajustes.md")
COLUMNAS = [
    "Iteración",
    "Qué falló",
    "Palanca",
    "Cambio",
    "Antes",
    "Después",
    "Decisión",
]
MINIMO_ESCENARIOS = 10
MINIMO_CATEGORIAS = 4
MINIMO_ITERACIONES = 2
OBLIGATORIAS = ("fuera de alcance", "error esperado", "control")
CIFRA = re.compile(r"(\d+) de (\d+)")


def escenarios_completos() -> tuple[bool, str]:
    ids = [e["id"] for e in ESCENARIOS]
    categorias = {e["categoria"] for e in ESCENARIOS}
    problemas: list[str] = []
    if len(ESCENARIOS) < MINIMO_ESCENARIOS:
        problemas.append(f"hay {len(ESCENARIOS)} escenarios y se piden {MINIMO_ESCENARIOS}")
    if len(set(ids)) != len(ids):
        problemas.append("hay identificadores repetidos")
    if len(categorias) < MINIMO_CATEGORIAS:
        problemas.append(f"hay {len(categorias)} categorias y se piden {MINIMO_CATEGORIAS}")
    faltan = [c for c in OBLIGATORIAS if c not in categorias]
    if faltan:
        problemas.append(f"faltan las categorias {faltan}")
    if problemas:
        return False, "; ".join(problemas)
    return True, f"{len(ESCENARIOS)} escenarios en {len(categorias)} categorias"


def filas_de_la_bitacora(raiz: Path = Path(".")) -> list[dict[str, str]] | None:
    archivo = raiz / BITACORA
    if not archivo.exists():
        return None
    filas: list[dict[str, str]] = []
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if celdas[0] == "Iteración" or set(celdas[0]) <= set("-: "):
            continue
        if len(celdas) == len(COLUMNAS):
            filas.append(dict(zip(COLUMNAS, celdas)))
    return filas


def bitacora_completa(raiz: Path = Path(".")) -> tuple[bool, str]:
    filas = filas_de_la_bitacora(raiz)
    if filas is None:
        return False, f"no existe {BITACORA}"
    if len(filas) < MINIMO_ITERACIONES:
        return False, f"hay {len(filas)} iteracion(es) y se piden {MINIMO_ITERACIONES}"
    problemas: list[str] = []
    mejoras = 0
    for f in filas:
        vacias = [c for c in COLUMNAS if not f[c]]
        antes, despues = CIFRA.search(f["Antes"]), CIFRA.search(f["Después"])
        if vacias:
            problemas.append(f"iteracion {f['Iteración']}: vacio {vacias}")
        elif not (antes and despues):
            problemas.append(f"iteracion {f['Iteración']}: Antes y Después se escriben como '9 de 12'")
        elif f["Decisión"].lower() not in ("conservar", "descartar"):
            problemas.append(f"iteracion {f['Iteración']}: Decisión debe ser conservar o descartar")
        elif f["Decisión"].lower() == "conservar" and int(despues.group(1)) > int(antes.group(1)):
            mejoras += 1
    if not problemas and mejoras == 0:
        problemas.append("ninguna iteracion conservada mejoró el resultado")
    if problemas:
        return False, "; ".join(problemas)
    return True, f"{len(filas)} iteraciones, {mejoras} con mejora conservada"


def solucion_responde() -> tuple[bool, str]:
    problemas: list[str] = []
    for nombre, base in ee.DESTINOS.items():
        try:
            r = httpx2.get(base + "/health", timeout=5)
            if r.status_code != 200:
                problemas.append(f"{nombre}: estado {r.status_code}")
        except httpx2.HTTPError:
            problemas.append(f"{nombre}: no responde")
    if problemas:
        return False, "; ".join(problemas) + " (docker compose up -d)"
    return True, "la interfaz y la API responden en /health"


def escenarios_cumplen() -> tuple[bool, str]:
    resultados = ee.correr()
    fallan = [r["id"] for r in resultados if r["motivos"]]
    total = len(resultados)
    if fallan:
        return False, f"{total - len(fallan)} de {total}; fallan {fallan}"
    return True, f"{total} de {total} escenarios cumplidos"


def repetible_y_coherente(raiz: Path = Path(".")) -> tuple[bool, str]:
    primera, segunda = ee.correr(), ee.correr()
    if ee.firma(primera) != ee.firma(segunda):
        return False, "dos corridas dieron resultados distintos"
    cumplidos = sum(1 for r in primera if not r["motivos"])
    conservadas = [
        f for f in (filas_de_la_bitacora(raiz) or []) if f["Decisión"].lower() == "conservar"
    ]
    cifra = CIFRA.search(conservadas[-1]["Después"]) if conservadas else None
    if not cifra:
        return False, "la bitácora no tiene una iteración conservada"
    anotado = (int(cifra.group(1)), int(cifra.group(2)))
    real = (cumplidos, len(primera))
    if anotado != real:
        return False, f"la bitácora dice {anotado[0]} de {anotado[1]} y la corrida da {real[0]} de {real[1]}"
    return True, f"dos corridas iguales; {real[0]} de {real[1]} como en la bitácora"


COMPROBACIONES = [
    ("EJE-1", "escenarios completos", escenarios_completos),
    ("EJE-2", "bitácora de ajustes", bitacora_completa),
    ("EJE-3", "la solución responde", solucion_responde),
    ("EJE-4", "los escenarios se cumplen", escenarios_cumplen),
    ("EJE-5", "repetible y coherente con la bitácora", repetible_y_coherente),
]


def ejecutar() -> bool:
    cumplidas = 0
    for id_, descripcion, prueba in COMPROBACIONES:
        try:
            ok, evidencia = prueba()
        except Exception as error:
            ok, evidencia = False, f"error: {error!r}"
        estado = "PASA " if ok else "FALLA"
        print(f"{estado} {id_} {descripcion} -> {evidencia}")
        cumplidas += 1 if ok else 0
        if id_ == "EJE-3" and not ok:
            break
    total = len(COMPROBACIONES)
    print(f"\n{cumplidas} de {total} comprobaciones cumplidas")
    return cumplidas == total


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar() else 1)
