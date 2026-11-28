"""Utilidad de diagnóstico para inspeccionar una petición HTTP aislada (U3.5 · Bloque 42)."""
from __future__ import annotations

import argparse
import json
import sys

import ejecutar_matriz


def main() -> int:
    parser = argparse.ArgumentParser(description="Envía una petición aislada al servicio.")
    parser.add_argument("metodo", choices=["GET", "POST", "PUT", "DELETE"])
    parser.add_argument("ruta", help="Ruta relativa, ej. /ask o /estudiantes/Sofía Rojas")
    parser.add_argument("--json", dest="cuerpo", default=None, help="Cuerpo JSON opcional")
    parser.add_argument("--url", default=None, help="URL base opcional del servicio en vivo")
    args = parser.parse_args()

    kwargs = {}
    if args.cuerpo:
        kwargs["json"] = json.loads(args.cuerpo)

    with ejecutar_matriz.abrir_cliente(args.url) as cliente:
        resp = cliente.request(args.metodo, args.ruta, **kwargs)
        print(f"HTTP {resp.status_code}")
        try:
            print(json.dumps(resp.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(resp.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
