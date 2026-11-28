"""Genera y comprueba `docs/api.md` ejecutando los ejemplos reales contra FastAPI (U3.6 · Bloque 45).

Uso:
    python generar_api_md.py             # escribe docs/api.md
    python generar_api_md.py --comprobar # falla con 1 si docs/api.md está desactualizado
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi.testclient import TestClient

from ejemplos_api import EJEMPLOS
from servicio.main import app

REPO_ROOT = Path(__file__).resolve().parent
DESTINO = REPO_ROOT / "docs" / "api.md"
TRACE_ID_RE = re.compile(r'"trace_id":\s*"[^"]+"')


def _normalizar_volatiles(texto: str) -> str:
    """Estabiliza trace_id para comparaciones deterministas de `--comprobar`."""
    return TRACE_ID_RE.sub('"trace_id": "<trace-id-generado>"', texto)


def _comando_curl(ejemplo: dict[str, Any]) -> str:
    ruta_codificada = quote(ejemplo["ruta"], safe="/")
    url = f"http://127.0.0.1:8000{ruta_codificada}"
    if ejemplo["metodo"] == "GET":
        return f"curl -s {url}"
    cuerpo = json.dumps(ejemplo.get("json", {}), ensure_ascii=False)
    return f"curl -s -X {ejemplo['metodo']} {url} -H 'Content-Type: application/json' -d '{cuerpo}'"


def generar_markdown() -> str:
    esquema = app.openapi()
    lineas: list[str] = [
        "# Referencia de la API HTTP",
        "",
        f"Generado automáticamente desde el contrato OpenAPI (`{esquema.get('info', {}).get('version', '0.2.0')}`) "
        "y verificado ejecutando cada ejemplo en vivo con `generar_api_md.py`.",
        "",
        "## Endpoints expuestos",
        "",
        "| Método | Ruta | Resumen |",
        "| --- | --- | --- |",
    ]

    for ruta, metodos in sorted(esquema.get("paths", {}).items()):
        for metodo, spec in sorted(metodos.items()):
            resumen = spec.get("summary", "").strip()
            lineas.append(f"| `{metodo.upper()}` | `{ruta}` | {resumen} |")

    lineas.extend(["", "## Ejemplos ejecutados", ""])

    with TestClient(app, raise_server_exceptions=False) as cliente:
        for ej in EJEMPLOS:
            kwargs: dict[str, Any] = {}
            if "json" in ej:
                kwargs["json"] = ej["json"]
            resp = cliente.request(ej["metodo"], ej["ruta"], **kwargs)
            try:
                cuerpo_str = json.dumps(resp.json(), ensure_ascii=False, indent=2)
            except Exception:
                cuerpo_str = resp.text
            cuerpo_str = _normalizar_volatiles(cuerpo_str)

            lineas.extend(
                [
                    f"### {ej['id']} — {ej['titulo']}",
                    "",
                    f"- **Petición:** `{ej['metodo']} {ej['ruta']}`",
                    f"- **Estado HTTP:** `{resp.status_code}`",
                    "",
                    "```bash",
                    _comando_curl(ej),
                    "```",
                    "",
                    "```json",
                    cuerpo_str,
                    "```",
                    "",
                ]
            )

    return "\n".join(lineas).rstrip() + "\n"


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera o comprueba docs/api.md.")
    parser.add_argument(
        "--comprobar",
        action="store_true",
        help="Verifica que docs/api.md coincide con las respuestas actuales.",
    )
    args = parser.parse_args(argumentos)

    nuevo = generar_markdown()
    if args.comprobar:
        if not DESTINO.exists():
            print(f"FALLA {DESTINO.name} no existe: ejecuta python generar_api_md.py")
            return 1
        actual = DESTINO.read_text(encoding="utf-8")
        if actual != nuevo:
            print(f"FALLA {DESTINO.name} esta desactualizado: ejecuta python generar_api_md.py")
            return 1
        print(f"PASA {DESTINO.name} coincide con los {len(EJEMPLOS)} ejemplos reales")
        print("1 de 1 comprobaciones cumplidas")
        return 0

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(nuevo, encoding="utf-8")
    print(f"Escrito {DESTINO}: {len(EJEMPLOS)} ejemplos ejecutados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
