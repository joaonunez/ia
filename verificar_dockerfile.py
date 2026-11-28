"""Verificador estático del Dockerfile y .dockerignore (U3.3 · Bloques 37-38).

Uso:
    python verificar_dockerfile.py
    python verificar_dockerfile.py interfaz/Dockerfile
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

RAIZ = Path(__file__).resolve().parent


def _leer_lineas_limpias(ruta: Path) -> list[str]:
    if not ruta.exists():
        return []
    lineas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        limpia = linea.strip()
        if limpia and not limpia.startswith("#"):
            lineas.append(limpia)
    return lineas


def comprobar_dockerfile(ruta_dockerfile: Path | None = None) -> list[tuple[str, bool, str]]:
    """Devuelve lista de `(regla, pasa, detalle)` sobre el Dockerfile indicado."""
    dockerfile = ruta_dockerfile if ruta_dockerfile is not None else (RAIZ / "Dockerfile")
    carpeta = dockerfile.parent
    dockerignore = carpeta / ".dockerignore"

    texto_df = dockerfile.read_text(encoding="utf-8") if dockerfile.exists() else ""
    lineas_df = _leer_lineas_limpias(dockerfile)
    lineas_di = set(_leer_lineas_limpias(dockerignore))

    resultados: list[tuple[str, bool, str]] = []

    # 1. Imagen base fija (sin :latest)
    from_match = re.search(r"^FROM\s+(\S+)", texto_df, re.MULTILINE)
    base = from_match.group(1) if from_match else ""
    ok_from = bool(base) and ":" in base and not base.endswith(":latest")
    resultados.append(("DF-01 imagen base con versión fija", ok_from, base or "falta FROM"))

    # 2. Caché optimizada: COPY requirements.txt -> pip install -> COPY código
    idx_req = next((i for i, l in enumerate(lineas_df) if l.startswith("COPY") and "requirements.txt" in l), -1)
    idx_pip = next((i for i, l in enumerate(lineas_df) if "pip install" in l), -1)
    idx_code = next(
        (i for i, l in enumerate(lineas_df) if l.startswith("COPY") and "requirements.txt" not in l),
        -1,
    )
    ok_cache = 0 <= idx_req < idx_pip < idx_code
    resultados.append(
        (
            "DF-02 requisitos instalados antes de copiar código",
            ok_cache,
            f"req={idx_req}, pip={idx_pip}, code={idx_code}",
        )
    )

    # 3. pip install --no-cache-dir
    ok_nocache = "--no-cache-dir" in texto_df
    resultados.append(
        ("DF-03 pip sin caché (--no-cache-dir)", ok_nocache, "--no-cache-dir presente" if ok_nocache else "falta")
    )

    # 4. Usuario sin privilegios
    user_match = re.search(r"^USER\s+(\S+)", texto_df, re.MULTILINE)
    usuario = user_match.group(1) if user_match else ""
    ok_user = bool(usuario) and usuario.lower() not in {"root", "0"}
    resultados.append(("DF-04 usuario sin privilegios (USER)", ok_user, f"USER {usuario}" if usuario else "falta USER"))

    # 5. HEALTHCHECK presente
    ok_health = "HEALTHCHECK" in texto_df and "/health" in texto_df
    resultados.append(("DF-05 HEALTHCHECK sobre /health", ok_health, "configurado" if ok_health else "falta HEALTHCHECK"))

    # 6. Escucha hacia afuera (0.0.0.0)
    ok_host = "0.0.0.0" in texto_df and "uvicorn" in texto_df
    resultados.append(
        ("DF-06 uvicorn escucha en 0.0.0.0", ok_host, "0.0.0.0 configurado" if ok_host else "falta --host 0.0.0.0")
    )

    # 7. .dockerignore excluye .env y .git
    requeridos_di = {".env", ".git"}
    faltan_di = sorted(requeridos_di - lineas_di)
    resultados.append(
        (
            "DF-07 .dockerignore excluye .env y .git",
            not faltan_di,
            "completo" if not faltan_di else f"faltan: {faltan_di}",
        )
    )

    return resultados


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    ruta = Path(args[0]) if args else (RAIZ / "Dockerfile")
    if not ruta.is_absolute():
        ruta = RAIZ / ruta
    resultados = comprobar_dockerfile(ruta)
    aprobadas = 0
    for regla, ok, detalle in resultados:
        estado = "PASA " if ok else "FALLA"
        print(f"{estado} {regla} -> {detalle}")
        if ok:
            aprobadas += 1
    print(f"\n{aprobadas} de {len(resultados)} reglas cumplidas")
    return 0 if aprobadas == len(resultados) else 1


if __name__ == "__main__":
    raise SystemExit(main())
