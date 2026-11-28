"""Verificador de ausencia de secretos en repositorio, plantillas y Docker (U3.3 · Bloque 38).

Uso:
    python buscar_secretos.py
    python buscar_secretos.py asistente-academico/api:0.3
"""
from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys

RAIZ = Path(__file__).resolve().parent

PATRONES_SECRETO: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("google_api_key", re.compile(r"AIza[0-9A-Za-z_-]{20,}")),
    ("openai_key", re.compile(r"sk-[0-9A-Za-z]{20,}")),
    ("private_key_header", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
)

DIRECTORIOS_EXCLUIDOS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "vectorstore"}


def _archivos_escaneables(raiz: Path) -> list[Path]:
    archivos: list[Path] = []
    for ruta in raiz.rglob("*"):
        if any(parte in DIRECTORIOS_EXCLUIDOS for parte in ruta.parts):
            continue
        if not ruta.is_file() or ruta.name == ".env":
            continue
        if ruta.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".pdf", ".pyc", ".sqlite3", ".bin"}:
            continue
        archivos.append(ruta)
    return archivos


def comprobar_gitignore(raiz: Path = RAIZ) -> tuple[bool, str]:
    gitignore = raiz / ".gitignore"
    if not gitignore.exists():
        return False, "no existe .gitignore"
    lineas = {l.strip() for l in gitignore.read_text(encoding="utf-8").splitlines()}
    ok = ".env" in lineas
    return ok, ".env excluido en .gitignore" if ok else "falta .env en .gitignore"


def comprobar_env_no_versionado(raiz: Path = RAIZ) -> tuple[bool, str]:
    r = subprocess.run(
        ["git", "-C", str(raiz), "ls-files", ".env"],
        capture_output=True,
        text=True,
        check=False,
    )
    ok = r.returncode == 0 and r.stdout.strip() == ""
    return ok, ".env no esta versionado en git" if ok else ".env figura versionado en git"


def comprobar_env_example(raiz: Path = RAIZ) -> tuple[bool, str]:
    ejemplo = raiz / ".env.example"
    if not ejemplo.exists():
        return False, "no existe .env.example"
    sospechosos: list[str] = []
    for linea in ejemplo.read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if not limpia or limpia.startswith("#") or "=" not in limpia:
            continue
        clave, valor = limpia.split("=", 1)
        if any(p in clave.upper() for p in ("KEY", "SECRET", "TOKEN", "PASSWORD")) and valor.strip():
            sospechosos.append(clave)
    return not sospechosos, ".env.example sin valores secretos" if not sospechosos else f"valores en: {sospechosos}"


def comprobar_codigo_sin_secretos(raiz: Path = RAIZ) -> tuple[bool, str]:
    hallazgos: list[str] = []
    for ruta in _archivos_escaneables(raiz):
        if ruta.name == "buscar_secretos.py":
            continue
        try:
            texto = ruta.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for nombre, patron in PATRONES_SECRETO:
            if patron.search(texto):
                hallazgos.append(f"{ruta.relative_to(raiz)}:{nombre}")
    return not hallazgos, "ningun patron de secreto en el repositorio" if not hallazgos else f"hallazgos: {hallazgos}"


def comprobar_docker_sin_secretos(raiz: Path = RAIZ, imagen: str | None = None) -> tuple[bool, str]:
    objetivos = [raiz / "Dockerfile", raiz / "interfaz" / "Dockerfile", raiz / "compose.yaml"]
    hallazgos: list[str] = []
    for ruta in objetivos:
        if not ruta.exists():
            continue
        texto = ruta.read_text(encoding="utf-8")
        for nombre, patron in PATRONES_SECRETO:
            if patron.search(texto):
                hallazgos.append(f"{ruta.relative_to(raiz)}:{nombre}")
    if hallazgos:
        return False, f"secretos en archivos Docker: {hallazgos}"

    if imagen:
        ins = subprocess.run(
            ["docker", "image", "inspect", imagen],
            capture_output=True,
            text=True,
            check=False,
        )
        if ins.returncode == 0:
            for nombre, patron in PATRONES_SECRETO:
                if patron.search(ins.stdout):
                    return False, f"secreto {nombre} encontrado en metadatos de imagen {imagen}"
            return True, f"archivos Docker e imagen {imagen} sin secretos"
    return True, "Dockerfile y compose.yaml sin secretos hardcodeados"


def ejecutar(raiz: Path = RAIZ, imagen: str | None = None) -> bool:
    comprobaciones = [
        ("SEC-1", ".gitignore excluye .env", lambda: comprobar_gitignore(raiz)),
        ("SEC-2", ".env fuera de git", lambda: comprobar_env_no_versionado(raiz)),
        ("SEC-3", ".env.example sin valores secretos", lambda: comprobar_env_example(raiz)),
        ("SEC-4", "repositorio sin claves hardcodeadas", lambda: comprobar_codigo_sin_secretos(raiz)),
        ("SEC-5", "Dockerfile y compose sin secretos", lambda: comprobar_docker_sin_secretos(raiz, imagen)),
    ]
    cumplidas = 0
    for id_, desc, fn in comprobaciones:
        ok, evidencia = fn()
        estado = "PASA " if ok else "FALLA"
        print(f"{estado} {id_} {desc} -> {evidencia}")
        if ok:
            cumplidas += 1
    print(f"\n{cumplidas} de {len(comprobaciones)} comprobaciones cumplidas")
    return cumplidas == len(comprobaciones)


if __name__ == "__main__":
    img = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(0 if ejecutar(RAIZ, img) else 1)
