"""Genera evidencia automática en `docs/registro_pruebas.md` contra el servidor real (U3.2 · Bloque 36).

Uso:
    uvicorn servicio.main:app --port 8000
    python registrar_pruebas.py http://127.0.0.1:8000
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import httpx2

from casos import CASOS, ejecutar_caso

SALIDA_POR_DEFECTO = Path(__file__).resolve().parent / "docs" / "registro_pruebas.md"


def verificar_cobertura(casos: list[dict[str, Any]]) -> list[str]:
    """Verifica cobertura mínima exigida por la actividad core de U3.2 Bloque 36."""
    errores: list[str] = []
    validos = [c for c in casos if str(c["id"]).startswith("V-")]
    invalidos = [c for c in casos if str(c["id"]).startswith("I-")]
    estados_invalidos = {c["estado"] for c in invalidos}

    if len(validos) < 3:
        errores.append(f"Se requieren al menos 3 casos válidos (V-); hay {len(validos)}.")
    if len(invalidos) < 5:
        errores.append(f"Se requieren al menos 5 casos inválidos (I-); hay {len(invalidos)}.")
    faltantes = {404, 405, 422} - estados_invalidos
    if faltantes:
        errores.append(f"Faltan casos inválidos que cubran los códigos HTTP: {sorted(faltantes)}.")
    return errores


def describir(caso: dict[str, Any]) -> str:
    """Resume la petición de un caso para la tabla de evidencia."""
    base = f"`{caso['metodo']} {caso['ruta']}`"
    if "json" in caso:
        cuerpo = str(caso["json"])
        if len(cuerpo) > 65:
            cuerpo = cuerpo[:62] + "..."
        return f"{base} · `{cuerpo}`"
    if "content" in caso:
        return f"{base} · cuerpo malformado"
    return base


def registrar(
    base_url: str = "http://127.0.0.1:8000",
    salida: Path = SALIDA_POR_DEFECTO,
) -> bool:
    """Ejecuta todos los casos contra `base_url` y escribe `docs/registro_pruebas.md`."""
    faltas = verificar_cobertura(CASOS)
    if faltas:
        for msg in faltas:
            print(f"ERROR DE COBERTURA: {msg}")
        return False

    filas: list[str] = []
    aprobados = 0
    with httpx2.Client(base_url=base_url, timeout=10.0) as cliente:
        salud = cliente.get("/health")
        if salud.status_code != 200:
            print(f"ERROR: /health respondió {salud.status_code}")
            return False
        version = salud.json().get("version", "desconocida")

        for caso in CASOS:
            ok, estado_real, detalle = ejecutar_caso(cliente, caso)
            estado_txt = "PASA" if ok else "FALLA"
            if ok:
                aprobados += 1
            filas.append(
                f"| {caso['id']} | {caso['descripcion']} | {describir(caso)} "
                f"| {caso['estado']} | {estado_real} | `{detalle}` | **{estado_txt}** |"
            )

    marca_tiempo = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    validos_n = sum(1 for c in CASOS if c["id"].startswith("V-"))
    invalidos_n = sum(1 for c in CASOS if c["id"].startswith("I-"))

    contenido = "\n".join(
        [
            "# Registro de pruebas HTTP — Asistente Académico IA (U3.2 · Bloque 36)",
            "",
            f"- **Fecha de ejecución:** {marca_tiempo}",
            f"- **Servidor probado:** `{base_url}` (`uvicorn servicio.main:app`, versión `{version}`)",
            "- **Cliente HTTP externo:** `httpx2` (`registrar_pruebas.py`)",
            f"- **Cobertura:** {validos_n} casos válidos (`V-`) y {invalidos_n} casos inválidos (`I-`), cubriendo códigos `200`, `404`, `405` y `422`.",
            f"- **Resultado global:** **{aprobados}/{len(CASOS)} casos aprobados**.",
            "",
            "| ID | Caso | Petición | Esperado | Recibido | Detalle | Resultado |",
            "|---|---|---|---:|---:|---|---|",
            *filas,
            "",
        ]
    )

    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(contenido, encoding="utf-8")
    print(f"Registro escrito en {salida} ({aprobados}/{len(CASOS)} PASA)")
    return aprobados == len(CASOS)


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    raise SystemExit(0 if registrar(url) else 1)
