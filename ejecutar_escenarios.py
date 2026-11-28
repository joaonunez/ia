"""Ejecuta los escenarios end-to-end contra la interfaz o la API (U3.4 · Bloques 40-41).

Uso:
    python ejecutar_escenarios.py [--destino interfaz|api] [--dos-veces]
"""
from __future__ import annotations

import os
import sys
import time
from typing import Any

import httpx2

from escenarios import ESCENARIOS

DESTINOS: dict[str, str] = {
    "interfaz": os.getenv("INTERFAZ_BASE_URL", "http://127.0.0.1:8080"),
    "api": os.getenv("API_BASE_URL", "http://127.0.0.1:8000"),
}


def enviar(base: str, pregunta: str, destino: str) -> Any:
    """Envía la consulta por el camino correspondiente al destino."""
    if destino == "interfaz":
        return httpx2.get(base + "/preguntar", params={"texto": pregunta}, timeout=10)
    return httpx2.post(base + "/ask", json={"pregunta": pregunta}, timeout=10)


def evaluar(escenario: dict[str, Any], respuesta: Any) -> list[str]:
    """Devuelve la lista de motivos de incumplimiento (vacía si pasa)."""
    motivos: list[str] = []
    if respuesta.status_code != escenario["estado"]:
        motivos.append(
            f"estado {respuesta.status_code}, se esperaba {escenario['estado']}"
        )
    texto = respuesta.text
    for esperado in escenario["contiene"]:
        if esperado not in texto:
            motivos.append(f"falta {esperado!r}")
    for prohibido in escenario.get("no_contiene", []):
        if prohibido in texto:
            motivos.append(f"no debia aparecer {prohibido!r}")
    if "fuentes" in escenario:
        try:
            fuentes = respuesta.json().get("fuentes")
        except ValueError:
            fuentes = None
        if fuentes != escenario["fuentes"]:
            motivos.append(f"fuentes {fuentes}, se esperaba {escenario['fuentes']}")
    return motivos


def correr(destino: str = "interfaz") -> list[dict[str, Any]]:
    """Ejecuta todos los escenarios y devuelve un resumen por cada uno."""
    base = DESTINOS[destino]
    resultados: list[dict[str, Any]] = []
    for e in ESCENARIOS:
        inicio = time.perf_counter()
        try:
            respuesta = enviar(base, e["pregunta"], destino)
            motivos = evaluar(e, respuesta)
            estado, cuerpo = respuesta.status_code, respuesta.text
        except httpx2.HTTPError as error:
            motivos = [f"sin respuesta: {type(error).__name__}"]
            estado, cuerpo = 0, ""
        ms = round((time.perf_counter() - inicio) * 1000)
        resultados.append(
            {
                "id": e["id"],
                "categoria": e["categoria"],
                "estado": estado,
                "ms": ms,
                "motivos": motivos,
                "cuerpo": cuerpo,
                "descripcion": e["descripcion"],
            }
        )
    return resultados


def imprimir(resultados: list[dict[str, Any]]) -> bool:
    for r in resultados:
        marca = "PASA " if not r["motivos"] else "FALLA"
        print(
            f"{marca} {r['id']} {r['categoria']:<16} {r['estado']:>3} "
            f"{r['ms']:>4} ms  {r['descripcion']}"
        )
        for motivo in r["motivos"]:
            print(f"      -> {motivo}")
    cumplidos = sum(1 for r in resultados if not r["motivos"])
    print(f"\n{cumplidos} de {len(resultados)} escenarios cumplidos")
    return cumplidos == len(resultados)


def firma(resultados: list[dict[str, Any]]) -> list[tuple[str, int, tuple[str, ...]]]:
    """Lo que debe repetirse idéntico en dos corridas consecutivas."""
    return [(r["id"], r["estado"], tuple(r["motivos"])) for r in resultados]


if __name__ == "__main__":
    destino_cli = "interfaz"
    if "--destino" in sys.argv:
        destino_cli = sys.argv[sys.argv.index("--destino") + 1]
    primera = correr(destino_cli)
    todo_bien = imprimir(primera)
    if "--dos-veces" in sys.argv:
        igual = firma(primera) == firma(correr(destino_cli))
        print("Segunda corrida: " + ("mismos resultados" if igual else "RESULTADOS DISTINTOS"))
        todo_bien = todo_bien and igual
    raise SystemExit(0 if todo_bien else 1)
