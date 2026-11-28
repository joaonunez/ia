"""Genera `docs/prueba_transferencia.md` con huella SHA-256 desde `transferencia.py` (U3.6 · Bloque 45)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from transferencia import PRUEBA

REPO_ROOT = Path(__file__).resolve().parent
DESTINO = REPO_ROOT / "docs" / "prueba_transferencia.md"


def huella(prueba: dict[str, Any] = PRUEBA) -> str:
    serializado = json.dumps(prueba, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()[:12]


def generar_markdown(prueba: dict[str, Any] = PRUEBA) -> str:
    h = huella(prueba)
    logradas = sum(1 for t in prueba["tareas"] if t["lograda"])
    lineas = [
        "# Registro de Prueba Cruzada de Transferencia",
        "",
        f"- **Fecha:** {prueba['fecha']}",
        f"- **Revisor:** {prueba['revisor']}",
        f"- **Duración total:** {prueba['duracion_minutos']} min",
        f"- **Preguntas al autor:** {prueba['preguntas_al_autor']}",
        f"- **Documentos usados:** {', '.join(f'`{d}`' for d in prueba['documentos_usados'])}",
        f"- **Tareas logradas:** {logradas} de {len(prueba['tareas'])}",
        f"- **Huella de la prueba:** {h}",
        "",
        "## Tareas ejecutadas",
        "",
        "| ID | Tarea | Lograda | Min | Nota |",
        "| --- | --- | --- | --- | --- |",
    ]
    for t in prueba["tareas"]:
        lineas.append(
            f"| {t['id']} | {t['tarea']} | {'Sí' if t['lograda'] else 'No'} | {t['minutos']} | {t['nota']} |"
        )

    lineas.extend(["", "## Observaciones y cierre", ""])
    for obs in prueba["observaciones"]:
        lim = f" · Limitación: `{obs['limitacion']}`" if obs.get("limitacion") else ""
        lineas.extend(
            [
                f"### {obs['id']} ({obs['tarea']}) — `{obs['causa']}` / `{obs['estado']}`{lim}",
                f"- **Observación:** {obs['descripcion']}",
                f"- **Acción:** {obs['accion']}",
                "",
            ]
        )

    return "\n".join(lineas).rstrip() + "\n"


def main() -> int:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(generar_markdown(PRUEBA), encoding="utf-8")
    print(f"Escrito {DESTINO} (huella {huella(PRUEBA)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
