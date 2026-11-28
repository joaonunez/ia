"""Ejecuta las sondas de alucinación y genera `docs/registro_alucinaciones.md` (U3.5 · Bloque 43)."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from alucinaciones import SONDAS
from dobles import ModeloAlucinador
from servicio import cadena, fundamentacion

REPO_ROOT = Path(__file__).resolve().parent
DESTINO = REPO_ROOT / "docs" / "registro_alucinaciones.md"


def evaluar_sondas() -> list[dict[str, Any]]:
    """Ejecuta cada sonda contra `fundamentacion` y contra la cadena completa."""
    resultados: list[dict[str, Any]] = []
    for sonda in SONDAS:
        fragmentos = cadena.recuperar(sonda["pregunta"])
        problemas = fundamentacion.problemas_de_respaldo(
            sonda["respuesta_modelo"], fragmentos, cadena.SIN_INFORMACION
        )
        codigos = [c for c, _ in problemas]
        respuesta_final, fuentes_finales = cadena.ejecutar(
            sonda["pregunta"], ModeloAlucinador(sonda["respuesta_modelo"])
        )
        contenida = respuesta_final == cadena.SIN_INFORMACION and fuentes_finales == []

        if sonda["detectable"]:
            ok = (sonda["codigo_esperado"] in codigos) and contenida
            estado = "PASA" if ok else "FALLA"
        else:
            ok = not codigos and not contenida and len(str(sonda.get("decision", "")).strip()) >= 20
            estado = "LIMITE" if ok else "FALLA"

        resultados.append(
            {
                "id": sonda["id"],
                "tipo": sonda["tipo"],
                "escenario": sonda["escenario"],
                "detectable": sonda["detectable"],
                "codigos_detectados": codigos,
                "contenida": contenida,
                "estado": estado,
                "decision": sonda.get("decision", ""),
            }
        )
    return resultados


def escribir_registro(resultados: list[dict[str, Any]]) -> Path:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    contenidas = sum(1 for r in resultados if r["estado"] == "PASA")
    limites = sum(1 for r in resultados if r["estado"] == "LIMITE")
    fallas = sum(1 for r in resultados if r["estado"] == "FALLA")

    lineas = [
        "# Registro de Sondas de Alucinación",
        "",
        f"- **Fecha de ejecución:** {fecha}",
        f"- **Sondas ejecutadas:** {len(resultados)}",
        f"- **Resultado:** {contenidas} contenidas mecánicamente · {limites} limitaciones declaradas · {fallas} fallas",
        "",
        "## Resultados",
        "",
        "| ID | Tipo | Detectable | Códigos detectados | Contenida | Estado | Escenario |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in resultados:
        cods = ", ".join(r["codigos_detectados"]) if r["codigos_detectados"] else "ninguno"
        lineas.append(
            f"| {r['id']} | {r['tipo']} | {'Sí' if r['detectable'] else 'No'} | {cods} | "
            f"{'Sí' if r['contenida'] else 'No'} | {r['estado']} | {r['escenario']} |"
        )

    limites_lista = [r for r in resultados if r["estado"] == "LIMITE"]
    if limites_lista:
        lineas.extend(["", "## Limitaciones reconocidas del detector mecánico", ""])
        for r in limites_lista:
            lineas.extend(
                [
                    f"### {r['id']} — `{r['tipo']}`",
                    f"- **Escenario:** {r['escenario']}",
                    f"- **Decisión:** {r['decision']}",
                    "",
                ]
            )

    DESTINO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return DESTINO


def main() -> int:
    parser = argparse.ArgumentParser(description="Evalúa sondas de alucinación.")
    parser.add_argument("--escribir", action="store_true", help="Escribe docs/registro_alucinaciones.md")
    args = parser.parse_args()

    resultados = evaluar_sondas()
    for r in resultados:
        print(f"[{r['estado']:6s}] {r['id']} ({r['tipo']}): codigos={r['codigos_detectados']} contenida={r['contenida']}")
    if args.escribir:
        ruta = escribir_registro(resultados)
        print(f"Registro escrito en {ruta}")

    fallas = [r for r in resultados if r["estado"] == "FALLA"]
    return 1 if fallas else 0


if __name__ == "__main__":
    sys.exit(main())
