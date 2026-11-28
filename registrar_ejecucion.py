"""Genera `docs/registro_ejecucion.md` con la evidencia de una corrida completa (U3.4 · Bloque 41).

Uso:
    python registrar_ejecucion.py

Escribe únicamente la zona automática (entre `<!-- AUTO:INICIO -->` y `<!-- AUTO:FIN -->`).
Las secciones manuales debajo de `<!-- AUTO:FIN -->` se conservan al re-ejecutar.
"""
from __future__ import annotations

import datetime
import json
import platform
import re
import subprocess
import sys
from pathlib import Path

import httpx2

import ejecutar_escenarios as ee
from buscar_secretos import ASIGNACION, CLAVE_GOOGLE

REGISTRO = Path("docs/registro_ejecucion.md")
BITACORA = Path("docs/bitacora_ajustes.md")
INICIO = "<!-- AUTO:INICIO -->"
FIN = "<!-- AUTO:FIN -->"

COMPONENTES: list[tuple[str, str, str]] = [
    ("Interfaz web", "real", "interfaz/main.py (FastAPI puerto 8080)"),
    ("API", "real", "servicio/main.py (FastAPI puerto 8000)"),
    ("Recuperación", "simulado", "corpus en memoria (src/rag_corpus.py + servicio/cadena.py)"),
    ("Datos de estudiantes", "simulado", "ESTUDIANTES_SIMULADOS en servicio/logica.py"),
]

DETALLE_MODELO: dict[str, str] = {
    "simulado": "ModeloSimulado, sin red ni clave",
    "respaldo": "ModeloRespaldo, porque el modelo real no está integrado aún",
    "real": "modelo real de Gemini",
    "ninguno": "ningún modelo disponible (HTTP 503)",
}

PARTE_MANUAL = """## Qué se observó

[COMPLETAR] Lo que viste al ejecutar y que las cifras no dicen.

## Qué no se probó

[COMPLETAR] Lo que esta ejecución no demuestra, en una o dos frases.

## Siguiente paso

[COMPLETAR] Una sola acción concreta para la próxima iteración.
"""


def comando(*args: str) -> tuple[int, str]:
    r = subprocess.run(args, capture_output=True, text=True, check=False)
    return r.returncode, (r.stdout + r.stderr).strip()


def commit_del_codigo() -> str:
    codigo, hash_corto = comando("git", "rev-parse", "--short", "HEAD")
    if codigo != 0:
        return "sin repositorio git"
    _, cambios = comando("git", "status", "--porcelain", "--", ".", f":!{REGISTRO}")
    estado = "con cambios sin confirmar" if cambios else "sin cambios"
    return f"{hash_corto} ({estado})"


def imagenes() -> str:
    codigo, texto = comando("docker", "compose", "ps", "--format", "json")
    if codigo == 0 and texto:
        filas = []
        for ln in texto.splitlines():
            ln = ln.strip()
            if ln.startswith("{"):
                try:
                    filas.append(json.loads(ln))
                except json.JSONDecodeError:
                    pass
        if filas:
            return ", ".join(f"{f['Image']} ({f.get('Health') or f.get('State')})" for f in filas)
    return "ejecución local uvicorn (api:8000, interfaz:8080)"


def modelo_activo() -> str:
    """Consulta a la API qué modelo está atendiendo realmente (nunca hardcodeado)."""
    try:
        datos = httpx2.get(ee.DESTINOS["api"] + "/health", timeout=5).json()
    except (httpx2.HTTPError, ValueError):
        return "desconocido"
    return str(datos.get("modelo_activo", "desconocido"))


def pruebas() -> tuple[int, int]:
    _, texto = comando(sys.executable, "-m", "pytest", "-q")
    pasan = re.search(r"(\d+) passed", texto)
    fallan = re.search(r"(\d+) failed", texto)
    return (
        int(pasan.group(1)) if pasan else 0,
        int(fallan.group(1)) if fallan else 0,
    )


def iteraciones() -> tuple[int, int]:
    if not BITACORA.exists():
        return 0, 0
    filas = [
        ln
        for ln in BITACORA.read_text(encoding="utf-8").splitlines()
        if ln.startswith("| ") and len(ln) > 2 and ln[2].isdigit()
    ]
    conservadas = sum(1 for ln in filas if "| conservar |" in ln)
    return len(filas), conservadas


def zona_automatica() -> str:
    resultados = ee.correr("interfaz")
    cumplidos = sum(1 for r in resultados if not r["motivos"])
    pasan, fallan = pruebas()
    hechas, conservadas = iteraciones()
    ahora = datetime.datetime.now(datetime.timezone.utc)
    modelo = modelo_activo()
    detalle_modelo = DETALLE_MODELO.get(modelo, "no se pudo consultar")
    filas_comp = [*COMPONENTES, ("Modelo", modelo, detalle_modelo)]

    lineas = [
        "## Ejecución",
        "",
        "| Campo | Valor |",
        "|---|---|",
        f"| Fecha (UTC) | {ahora:%Y-%m-%d %H:%M:%S} |",
        f"| Commit del código | {commit_del_codigo()} |",
        f"| Python | {platform.python_version()} |",
        f"| Imágenes | {imagenes()} |",
        "",
        "## Componentes",
        "",
        "| Componente | Modo | Detalle |",
        "|---|---|---|",
        *[f"| {c} | {m} | {d} |" for c, m, d in filas_comp],
        "",
        "## Resultados",
        "",
        f"- Escenarios: {cumplidos} de {len(resultados)} cumplidos (por la interfaz).",
        f"- Pruebas automáticas: {pasan} pasan, {fallan} fallan.",
        f"- Ajustes: {hechas} iteraciones, {conservadas} conservadas (ver docs/bitacora_ajustes.md).",
        "",
        "| Escenario | Categoría | Resultado |",
        "|---|---|---|",
    ]
    for r in resultados:
        veredicto = "pasa" if not r["motivos"] else "; ".join(r["motivos"])
        lineas.append(f"| {r['id']} | {r['categoria']} | {veredicto} |")
    return "\n".join(lineas)


def con_forma_de_secreto(texto: str) -> bool:
    return bool(CLAVE_GOOGLE.search(texto) or ASIGNACION.search(texto))


def armar(zona: str, previo: str) -> str:
    if previo and INICIO in previo and FIN in previo:
        antes, _, resto = previo.partition(INICIO)
        _, _, despues = resto.partition(FIN)
        return f"{antes}{INICIO}\n{zona}\n{FIN}{despues}"
    return f"# Registro de ejecución\n\n{INICIO}\n{zona}\n{FIN}\n\n{PARTE_MANUAL}"


def main() -> int:
    try:
        r = httpx2.get(ee.DESTINOS["interfaz"] + "/health", timeout=5)
        if r.status_code != 200:
            print(f"La interfaz respondió {r.status_code}: verifica los servicios.")
            return 1
    except httpx2.HTTPError:
        print("La solución no responde: levanta la API y la interfaz (docker compose up -d o uvicorn).")
        return 1

    zona = zona_automatica()
    previo = REGISTRO.read_text(encoding="utf-8") if REGISTRO.exists() else ""
    texto = armar(zona, previo)
    if con_forma_de_secreto(texto):
        print("El registro tiene forma de secreto: no se escribió.")
        return 1
    REGISTRO.parent.mkdir(parents=True, exist_ok=True)
    REGISTRO.write_text(texto, encoding="utf-8")
    print(f"Registro escrito en {REGISTRO}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
