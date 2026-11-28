"""Verificador completo de las 5 secciones de la Ficha y la revisión cruzada (U3.1 · Bloque 34)."""
from __future__ import annotations

import os
import re
import sys

from ficha_datos import RUTA, cargar
from verificar_ficha import verificar

REVISION = "docs/revision_alcance.md"
MIN_HITOS, MAX_HITOS = 3, 6


def verificar_pendientes(ficha: dict) -> list[str]:
    errores: list[str] = []
    for numero in (4, 5):
        texto = ficha[f"texto{numero}"]
        if "[PENDIENTE" in texto or "[COMPLETAR" in texto:
            errores.append(f"la seccion {numero} todavia tiene marcas")
    return errores


def verificar_criterios(ficha: dict) -> tuple[list[str], list[str]]:
    errores: list[str] = []
    avisos: list[str] = []
    existentes = set(ficha["rf"]) | set(ficha["rnf"])
    if not ficha["criterios"]:
        errores.append("la seccion 4 no tiene criterios (formato CA-NN)")

    escritos = len(re.findall(r"(?m)^- CA", ficha["texto4"]))
    if escritos != len(ficha["criterios"]):
        errores.append(
            f"{escritos - len(ficha['criterios'])} criterio(s) "
            "no siguen el formato '- CA-NN (RF-NN): texto'"
        )

    cubiertos: set[str] = set()
    for c in ficha["criterios"]:
        if not c["cubre"]:
            errores.append(f"{c['id']} no indica que RF o RNF cubre")
        for rid in c["cubre"]:
            if rid not in existentes:
                errores.append(f"{c['id']} cubre {rid}, que no existe")
        cubiertos.update(c["cubre"])
        if not re.search(r'\d|"', c["texto"]):
            avisos.append(f"{c['id']} no tiene ningun dato concreto")

    exigidos = ficha["cajones"]["Imprescindible"] + list(ficha["rnf"])
    for rid in exigidos:
        if rid not in cubiertos:
            errores.append(f"{rid} no tiene criterio de aceptacion")
    return errores, avisos


def verificar_plan(ficha: dict) -> list[str]:
    errores: list[str] = []
    hitos = ficha["hitos"]
    ids_ca = {c["id"] for c in ficha["criterios"]}
    existentes = set(ficha["rf"]) | set(ficha["rnf"])

    escritos = len(re.findall(r"(?m)^- H\d", ficha["texto5"]))
    if escritos != len(hitos):
        errores.append(
            f"{escritos - len(hitos)} hito(s) no siguen el formato "
            "'- H1 (3 h): descripcion. Cubre: ... Se comprueba con: ...'"
        )

    if not MIN_HITOS <= len(hitos) <= MAX_HITOS:
        errores.append(
            f"hay {len(hitos)} hitos y se piden entre {MIN_HITOS} y {MAX_HITOS}"
        )

    if ficha["disponibles"] is None or ficha["margen"] is None:
        errores.append(
            "faltan las lineas 'Horas disponibles:' y 'Margen de imprevistos:'"
        )
    else:
        tope = ficha["disponibles"] - ficha["margen"]
        total = sum(h["horas"] for h in hitos)
        if total > tope:
            errores.append(f"los hitos suman {total:.1f} h y el tope es {tope:.1f} h")

    cubiertos: set[str] = set()
    probados: set[str] = set()
    for h in hitos:
        if not h["cubre"]:
            errores.append(f"{h['id']} no indica que cubre")
        if not h["criterios"]:
            errores.append(f"{h['id']} no tiene criterio de aceptacion")
        for rid in h["cubre"]:
            if rid not in existentes:
                errores.append(f"{h['id']} cubre {rid}, que no existe")
        for cid in h["criterios"]:
            if cid not in ids_ca:
                errores.append(f"{h['id']} usa {cid}, que no existe")
        cubiertos.update(h["cubre"])
        probados.update(h["criterios"])

    for rid in ficha["cajones"]["Imprescindible"]:
        if rid not in cubiertos:
            errores.append(f"{rid} imprescindible sin hito que lo cubra")

    for cid in sorted(ids_ca - probados):
        errores.append(f"{cid} no lo comprueba ningun hito")

    return errores


def verificar_revision(ruta: str = REVISION) -> list[str]:
    if not os.path.exists(ruta):
        return [f"falta {ruta}: registra la revision cruzada"]
    with open(ruta, encoding="utf-8") as archivo:
        texto = archivo.read()
    patron = r"(?m)^- Hallazgo \d+(?: \([^)]*\))?: .+$"
    hallazgos = re.findall(patron, texto)
    decisiones = re.findall(
        r"(?m)^  Decisión: (?:aceptado|rechazado|aplazado)\b", texto
    )
    errores: list[str] = []
    if len(hallazgos) < 2:
        errores.append(f"hay {len(hallazgos)} hallazgos y se piden 2")
    if len(decisiones) != len(hallazgos):
        errores.append("cada hallazgo necesita su linea 'Decisión:'")
    return errores


if __name__ == "__main__":
    if not os.path.exists(RUTA):
        sys.exit(f"No existe {RUTA}. Ejecuta el script desde la raiz.")
    with open(RUTA, encoding="utf-8") as archivo:
        errores, avisos = verificar(archivo.read())
    if not errores:
        ficha = cargar()
        errores = verificar_pendientes(ficha)
    if not errores:
        errores, avisos_ca = verificar_criterios(ficha)
        errores += verificar_plan(ficha)
        avisos += avisos_ca
    if not errores:
        errores = verificar_revision()
    for aviso in avisos:
        print("AVISO:", aviso)
    for error in errores:
        print("ERROR:", error)
    if errores:
        print(f"\n{len(errores)} problema(s) por resolver")
        sys.exit(1)
    print("Ficha verificada: las cinco secciones son coherentes")
