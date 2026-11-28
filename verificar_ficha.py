"""Verificador de estructura de las secciones 1 a 3 de la Ficha de Diseño Funcional (U3.1 · Bloque 33)."""
from __future__ import annotations

import os
import re
import sys
import unicodedata

RUTA = "docs/ficha_diseno_funcional.md"
SECCIONES = {
    1: "problema",
    2: "requerimientos",
    3: "arquitectura",
    4: "criterios",
    5: "plan",
}
MAX_IMPRESCINDIBLES = 5
PALABRAS_SOLUCION = [
    "chatbot",
    "rag",
    "modelo",
    "inteligencia artificial",
    "llm",
]


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sin_tildes if unicodedata.category(c) != "Mn").lower()


def leer_secciones(texto: str) -> dict[int, tuple[str, str]]:
    secciones: dict[int, tuple[str, str]] = {}
    for bloque in re.split(r"(?m)^## ", texto)[1:]:
        encabezado, _, cuerpo = bloque.partition("\n")
        m = re.match(r"(\d)\.", encabezado.strip())
        if m:
            secciones[int(m.group(1))] = (
                normalizar(encabezado),
                cuerpo.strip(),
            )
    return secciones


def verificar(texto: str) -> tuple[list[str], list[str]]:
    errores: list[str] = []
    avisos: list[str] = []
    secciones = leer_secciones(texto)

    for numero, clave in SECCIONES.items():
        if numero not in secciones or clave not in secciones[numero][0]:
            errores.append(f"falta la seccion {numero} ({clave})")

    for numero in (1, 2, 3):
        if numero in secciones and "[COMPLETAR" in secciones[numero][1]:
            errores.append(f"la seccion {numero} todavia tiene marcas [COMPLETAR]")

    if errores:
        return errores, avisos

    problema = normalizar(secciones[1][1])
    for palabra in PALABRAS_SOLUCION:
        if re.search(rf"\b{palabra}\b", problema):
            avisos.append(f"el problema menciona la solucion ('{palabra}')")

    req = secciones[2][1]
    rf = dict(re.findall(r"(?m)^- (RF-\d{2}): (.+)$", req))
    rnf = dict(re.findall(r"(?m)^- (RNF-\d{2}): (.+)$", req))

    if len(rf) < 3:
        errores.append(f"hay {len(rf)} RF y se piden al menos 3")
    if len(rnf) < 2:
        errores.append(f"hay {len(rnf)} RNF y se piden al menos 2")

    for rid, texto_rnf in rnf.items():
        if not re.search(r"\d", texto_rnf):
            errores.append(f"{rid} no tiene ningun numero: no se puede comprobar")

    cajones: dict[str, list[str]] = {}
    for nombre in ("Imprescindible", "Deseable", "Fuera de alcance"):
        m = re.search(rf"(?m)^{nombre}:\s*(.*)$", req)
        cajones[nombre] = re.findall(r"RF-\d{2}", m.group(1)) if m else []
        if not m:
            errores.append(f"falta la linea '{nombre}:' en el alcance")

    if not cajones["Imprescindible"]:
        errores.append("el MVP no tiene ningun RF imprescindible")

    n_imp = len(cajones["Imprescindible"])
    if n_imp > MAX_IMPRESCINDIBLES:
        errores.append(
            f"el MVP tiene {n_imp} imprescindibles (maximo orientativo: {MAX_IMPRESCINDIBLES})"
        )

    clasificados = [r for lista in cajones.values() for r in lista]
    for rid in clasificados:
        if rid not in rf:
            errores.append(f"{rid} aparece en el alcance pero no esta definido")

    for rid in rf:
        veces = clasificados.count(rid)
        if veces != 1:
            errores.append(f"{rid} debe estar en exactamente un cajon (esta en {veces})")

    arquitectura = secciones[3][1]
    imagenes = re.findall(r"docs/[\w\-./]+\.(?:png|jpg|jpeg)", arquitectura)
    if not imagenes:
        errores.append("la seccion 3 no referencia ningun diagrama en docs/")
    for ruta in imagenes:
        if not os.path.exists(ruta):
            errores.append(f"el diagrama {ruta} no existe en el repositorio")

    return errores, avisos


if __name__ == "__main__":
    if not os.path.exists(RUTA):
        sys.exit(f"No existe {RUTA}. Ejecuta el script desde la raiz del repositorio.")
    with open(RUTA, encoding="utf-8") as archivo:
        errores, avisos = verificar(archivo.read())
    for aviso in avisos:
        print("AVISO:", aviso)
    for error in errores:
        print("ERROR:", error)
    if errores:
        print(f"\n{len(errores)} problema(s) por resolver")
        sys.exit(1)
    print("Ficha verificada: secciones 1 a 3 completas")
