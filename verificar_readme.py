"""Verificador del README técnico — reglas README-1 a README-8 (U3.6 · Bloque 44)."""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from buscar_secretos import ASIGNACION, CLAVE_GOOGLE

REPO_ROOT = Path(__file__).resolve().parent
README = REPO_ROOT / "README.md"
DOCKERFILE = REPO_ROOT / "Dockerfile"
COMPOSE = REPO_ROOT / "compose.yaml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"

SECCIONES_OBLIGATORIAS = (
    "Requisitos",
    "Instalación",
    "Configuración",
    "Cómo arrancar",
    "Cómo comprobar",
    "Pruebas",
    "Decisiones",
    "Limitaciones",
    "Estructura",
    "Problemas frecuentes",
)

RUTA_RE = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|md|yaml|yml|txt|png|json|example)|(?:servicio|interfaz|docs|tests)/)`")


def _normal(texto: str) -> str:
    n = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in n if not unicodedata.combining(c)).casefold().strip()


def comprobar_readme1(texto: str) -> tuple[bool, str]:
    encabezados = [_normal(h) for h in re.findall(r"^##\s+(.+)$", texto, re.M)]
    faltan = [s for s in SECCIONES_OBLIGATORIAS if not any(_normal(s) in h for h in encabezados)]
    if faltan:
        return False, f"faltan secciones: {faltan}"
    return True, f"las {len(SECCIONES_OBLIGATORIAS)} secciones obligatorias están presentes"


def comprobar_readme2(texto: str) -> tuple[bool, str]:
    vars_env = re.findall(r"^([A-Z][A-Z0-9_]+)=", ENV_EXAMPLE.read_text(encoding="utf-8"), re.M)
    faltan: list[str] = []
    for var in vars_env:
        patron = re.compile(rf"`{re.escape(var)}`[^\n]*(?:secreto|configuraci[oó]n)", re.I)
        if not patron.search(texto):
            faltan.append(var)
    if faltan:
        return False, f"variables sin clasificación (secreto/configuración): {faltan}"
    return True, f"variables {vars_env} clasificadas como secreto o configuración"


def comprobar_readme3(texto: str) -> tuple[bool, str]:
    esperados = ("docker compose up -d --build", "uvicorn servicio.main:app", "pytest")
    faltan = [cmd for cmd in esperados if cmd not in texto]
    if faltan:
        return False, f"faltan comandos clave: {faltan}"
    return True, "comandos de arranque Docker, uvicorn local y pytest documentados"


def comprobar_readme4(texto: str) -> tuple[bool, str]:
    faltan: list[str] = []
    for ruta in sorted(set(RUTA_RE.findall(texto))):
        if not (REPO_ROOT / ruta).exists():
            faltan.append(ruta)
    if faltan:
        return False, f"no existe {', '.join(faltan)}"
    return True, "todas las rutas citadas en README.md existen en el repositorio"


def comprobar_readme5(texto: str) -> tuple[bool, str]:
    puertos = sorted(set(re.findall(r'"(\d+):\d+"', COMPOSE.read_text(encoding="utf-8"))))
    faltan = [p for p in puertos if p not in texto]
    if faltan:
        return False, f"puertos de compose.yaml ausentes: {faltan}"
    return True, f"puertos {puertos} coherentes con compose.yaml"


def comprobar_readme6(texto: str) -> tuple[bool, str]:
    if CLAVE_GOOGLE.search(texto) or ASIGNACION.search(texto):
        return False, "posible secreto detectado en README.md"
    return True, "sin secretos en README.md"


def comprobar_readme7(texto: str) -> tuple[bool, str]:
    m = re.search(r"FROM\s+python:(\d+\.\d+)", DOCKERFILE.read_text(encoding="utf-8"))
    if not m:
        return False, "no se pudo leer la versión de Python desde Dockerfile"
    ver = m.group(1)
    if ver not in texto:
        return False, f"README.md no menciona Python {ver} de Dockerfile"
    return True, f"versión Python {ver} coincide con Dockerfile"


def comprobar_readme8() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-x", "tests/parciales/test_cadena.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if proc.returncode != 0:
        return False, f"pytest falló con código {proc.returncode}"
    return True, "pruebas base ejecutables sin red en verde"


def verificar() -> list[tuple[str, bool, str]]:
    texto = README.read_text(encoding="utf-8")
    return [
        ("README-1", *comprobar_readme1(texto)),
        ("README-2", *comprobar_readme2(texto)),
        ("README-3", *comprobar_readme3(texto)),
        ("README-4", *comprobar_readme4(texto)),
        ("README-5", *comprobar_readme5(texto)),
        ("README-6", *comprobar_readme6(texto)),
        ("README-7", *comprobar_readme7(texto)),
        ("README-8", *comprobar_readme8()),
    ]


def main() -> int:
    comprobaciones = verificar()
    ok_count = 0
    for codigo, ok, detalle in comprobaciones:
        marca = "PASA " if ok else "FALLA"
        print(f"{marca} {codigo} -> {detalle}")
        if ok:
            ok_count += 1
    print(f"\n{ok_count} de {len(comprobaciones)} comprobaciones cumplidas")
    return 0 if ok_count == len(comprobaciones) else 1


if __name__ == "__main__":
    sys.exit(main())
