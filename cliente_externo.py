"""Cliente HTTP externo con httpx2 para probar el servicio levantado (U3.2 · Bloque 36).

Uso:
    uvicorn servicio.main:app --port 8000
    python cliente_externo.py http://127.0.0.1:8000
"""
from __future__ import annotations

import sys

import httpx2

from casos import CASOS, ejecutar_caso


def main(base_url: str = "http://127.0.0.1:8000") -> int:
    with httpx2.Client(base_url=base_url, timeout=10.0) as cliente:
        try:
            salud = cliente.get("/health")
        except Exception as exc:
            print(f"ERROR: no se pudo conectar con {base_url}/health ({type(exc).__name__}: {exc})")
            return 2

        if salud.status_code != 200:
            print(f"ERROR: /health respondió {salud.status_code}")
            return 2

        aprobados = 0
        for caso in CASOS:
            ok, estado, detalle = ejecutar_caso(cliente, caso)
            marca = "PASA " if ok else "FALLA"
            print(f"{marca} {caso['id']:4s} [{estado}] {caso['descripcion']} -> {detalle}")
            if ok:
                aprobados += 1

        print(f"\nResultado cliente externo ({base_url}): {aprobados}/{len(CASOS)} casos aprobados")
        return 0 if aprobados == len(CASOS) else 1


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    raise SystemExit(main(url))
