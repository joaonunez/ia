"""Verifica la composición completa en Docker Compose de extremo a extremo (U3.3 · Bloque 38)."""
from __future__ import annotations

import json
import subprocess
import sys

import httpx2

from casos import CASOS, ejecutar_caso

API = "http://127.0.0.1:8000"
INTERFAZ = "http://127.0.0.1:8080"
PREGUNTA = "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"


def compose(*args: str) -> tuple[int, str]:
    r = subprocess.run(["docker", "compose", *args], capture_output=True, text=True, check=False)
    return r.returncode, (r.stdout + r.stderr).strip()


def ultima_linea(texto: str) -> str:
    lineas = [ln for ln in texto.splitlines() if ln.strip()]
    return lineas[-1][:150] if lineas else "sin mensaje"


def configuracion_valida() -> tuple[bool, str]:
    codigo, texto = compose("config", "--quiet")
    if codigo != 0:
        return False, ultima_linea(texto)
    return True, "compose.yaml es valido"


def arranca() -> tuple[bool, str]:
    codigo, texto = compose("up", "-d", "--build", "--wait", "--wait-timeout", "120")
    if codigo != 0:
        return False, ultima_linea(texto)
    return True, "docker compose up --wait termino sin errores"


def servicios_sanos() -> tuple[bool, str]:
    _, texto = compose("ps", "--format", "json")
    filas = [json.loads(ln) for ln in texto.splitlines() if ln.strip()]
    estados = {f["Service"]: f.get("Health") or f.get("State") for f in filas}
    ok = bool(estados) and set(estados.values()) == {"healthy"}
    return ok, f"servicios: {estados}"


def api_responde() -> tuple[bool, str]:
    r = httpx2.get(API + "/health", timeout=5)
    return r.status_code == 200, f"GET {API}/health -> {r.json()}"


def interfaz_llega_a_api() -> tuple[bool, str]:
    r = httpx2.get(INTERFAZ + "/preguntar", params={"texto": PREGUNTA}, timeout=5)
    ok = r.status_code == 200 and "fuentes" in r.json()
    return ok, f"estado {r.status_code}: {r.text[:60]}"


def casos_pasan() -> tuple[bool, str]:
    with httpx2.Client(base_url=API, timeout=10) as cliente:
        resultados = [ejecutar_caso(cliente, c) for c in CASOS]
    bien = sum(1 for ok, _, _ in resultados if ok)
    return bien == len(CASOS), f"{bien} de {len(CASOS)} casos en la API"


def baja_limpia() -> tuple[bool, str]:
    compose("down")
    _, restantes = compose("ps", "-q")
    return restantes == "", "no queda ningun contenedor del proyecto"


COMPROBACIONES = [
    ("STK-1", "compose.yaml valido", configuracion_valida),
    ("STK-2", "los servicios arrancan", arranca),
    ("STK-3", "todos los servicios sanos", servicios_sanos),
    ("STK-4", "la API responde", api_responde),
    ("STK-5", "la interfaz llega a la API", interfaz_llega_a_api),
    ("STK-6", "la tabla de casos pasa", casos_pasan),
    ("STK-7", "se apaga sin dejar restos", baja_limpia),
]


def ejecutar() -> bool:
    cumplidas = 0
    try:
        for i, (id_, descripcion, prueba) in enumerate(COMPROBACIONES):
            try:
                ok, evidencia = prueba()
            except Exception as error:
                ok, evidencia = False, f"error: {error!r}"
            estado = "PASA " if ok else "FALLA"
            print(f"{estado} {id_} {descripcion} -> {evidencia}")
            cumplidas += 1 if ok else 0
            if i <= 1 and not ok:
                break
    finally:
        compose("down")
    total = len(COMPROBACIONES)
    print(f"\n{cumplidas} de {total} comprobaciones cumplidas")
    return cumplidas == total


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar() else 1)
