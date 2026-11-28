"""Cuenta fricciones por sección en `docs/diario_de_friccion.md` y valida contra README (U3.6 · Bloque 44)."""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DIARIO = REPO_ROOT / "docs" / "diario_de_friccion.md"


def _normal(texto: str) -> str:
    n = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in n if not unicodedata.combining(c)).casefold().strip()


def leer_filas(ruta: Path = DIARIO) -> list[tuple[str, str, str, str]]:
    filas: list[tuple[str, str, str, str]] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        s = linea.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        celdas = [c.strip() for c in s.strip("|").split("|")]
        if len(celdas) == 4 and celdas[0].isdigit():
            filas.append((celdas[0], celdas[1], celdas[2], celdas[3]))
    return filas


def encabezados_readme(ruta_readme: Path) -> set[str]:
    texto = ruta_readme.read_text(encoding="utf-8")
    return {_normal(m) for m in re.findall(r"^##\s+(.+)$", texto, re.M)}


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cuenta fricciones por sección del diario.")
    parser.add_argument("--diario", default=str(DIARIO))
    parser.add_argument("--readme", default=None)
    args = parser.parse_args(argumentos)

    filas = leer_filas(Path(args.diario))
    conteo = Counter(f[3] for f in filas)
    print(f"Fricciones registradas: {len(filas)}")
    for seccion, n in conteo.most_common():
        print(f"  - {seccion}: {n}")

    if args.readme:
        titulos = encabezados_readme(Path(args.readme))
        faltan = [s for s in conteo if _normal(s) not in titulos]
        if faltan:
            print(f"FALLA secciones ausentes en README: {faltan}")
            return 1
        print(f"PASA todas las secciones del diario existen en {args.readme}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
