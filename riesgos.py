"""Matriz de Riesgos con mitigaciones verificables (Core U3.5 · Bloque 43 · id=25337).

Genera `docs/matriz_riesgos.md` ordenado por riesgo residual descendente con huella SHA-256.
Uso:
    python riesgos.py --escribir
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent
DESTINO = REPO_ROOT / "docs" / "matriz_riesgos.md"
ESTADOS_VALIDOS = ("verificada", "parcial", "aceptada")


def inherente(riesgo: dict[str, Any]) -> int:
    return int(riesgo["probabilidad"]) * int(riesgo["impacto"])


def categoria(puntaje: int) -> str:
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def huella(riesgos: list[dict[str, Any]]) -> str:
    serializado = json.dumps(riesgos, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()[:12]


RIESGOS: list[dict[str, Any]] = [
    {
        "id": "R-01",
        "riesgo": "Inyección directa de instrucciones y ofuscación en preguntas del usuario",
        "probabilidad": 4,
        "impacto": 5,
        "mitigacion": (
            "Normalización Unicode NFKD + casefold y 4 reglas de entrada en `servicio/seguridad.py`, "
            "más limpieza de salida en profundidad y ejecución en modo solo lectura."
        ),
        "evidencia": ["ataques:A-01", "ataques:A-04", "ataques:A-05", "ataques:A-07", "matriz:MP-03"],
        "estado": "parcial",
        "residual": 6,
        "limites": ["A-07"],
        "nota": (
            "Las variantes con letras separadas por guiones (A-07) evaden las expresiones regulares "
            "de entrada; quedan contenidas por limpieza de salida, compuerta de respaldo y solo lectura."
        ),
        "supervision": "",
    },
    {
        "id": "R-02",
        "riesgo": "Extracción de instrucciones internas del sistema o secretos mediante el modelo",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "Bloqueo en entrada (`pedir_instrucciones`, `pedir_secretos`) y capa independiente "
            "`limpiar_salida()` que redacta `INSTRUCCION` y claves `AIza...`/`sk-...`."
        ),
        "evidencia": ["ataques:A-02", "ataques:A-03", "fuga:F-03"],
        "estado": "verificada",
        "residual": 3,
        "limites": [],
        "nota": "",
        "supervision": "",
    },
    {
        "id": "R-03",
        "riesgo": "Alucinación cualitativa o cifras inventadas en letras no detectables mecánicamente",
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": (
            "Compuerta mecánica `problemas_de_respaldo` bloquea cifras en dígitos, fuentes falsas y "
            "respuestas sin fragmentos; los casos semánticos quedan bajo revisión humana obligatoria."
        ),
        "evidencia": ["alucinacion:H-01", "alucinacion:H-02", "alucinacion:H-03", "alucinacion:H-04", "alucinacion:H-05"],
        "estado": "parcial",
        "residual": 9,
        "limites": ["H-04", "H-05"],
        "nota": (
            "Las afirmaciones cualitativas agregadas (H-04) y cifras escritas en palabras (H-05) "
            "no son detectadas por reglas léxicas; se documentan como limitación activa del detector."
        ),
        "supervision": (
            "El gestor académico debe validar toda respuesta con la fuente citada antes de emitir "
            "comunicaciones formales a apoderados y realizar muestreo semanal de 10 trazas."
        ),
    },
    {
        "id": "R-04",
        "riesgo": "Inyección indirecta incrustada en documentos envenenados del corpus",
        "probabilidad": 3,
        "impacto": 5,
        "mitigacion": (
            "`sin_fragmentos_sospechosos()` filtra cada fragmento recuperado antes de construir "
            "el prompt y descarta cualquier documento que dispare reglas de inyección."
        ),
        "evidencia": ["ataques:A-06"],
        "estado": "verificada",
        "residual": 3,
        "limites": [],
        "nota": "",
        "supervision": "",
    },
    {
        "id": "R-05",
        "riesgo": "Exposición de PII o texto crudo de consultas en logs y respuestas de error 422",
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": (
            "Logging estructurado con longitudes y huellas SHA-256 (sin texto crudo ni correos) y "
            "manejador unificado `servicio/errores.py` que omite valores de entrada y stacktraces."
        ),
        "evidencia": ["fuga:F-01", "fuga:F-02", "matriz:MP-04"],
        "estado": "verificada",
        "residual": 2,
        "limites": [],
        "nota": "",
        "supervision": "",
    },
    {
        "id": "R-06",
        "riesgo": "Falla de recuperación ante sinónimos o paráfrasis sin palabras clave literales",
        "probabilidad": 3,
        "impacto": 3,
        "mitigacion": (
            "Normalización Unicode NFD para tildes combinantes en modo simulado; recuperación "
            "semántica con embeddings en Chroma cuando se activa `USE_LIVE_RAG=true`."
        ),
        "evidencia": ["matriz:MP-06", "matriz_modelo:MP-07", "matriz_modelo:MP-08"],
        "estado": "parcial",
        "residual": 6,
        "limites": ["MP-08"],
        "nota": (
            "En modo simulado sin embeddings la paráfrasis pura sin palabras clave compartidas "
            "(MP-08) devuelve SIN_INFORMACION en lugar de inventar; aceptado para entorno sin red."
        ),
        "supervision": "",
    },
    {
        "id": "R-07",
        "riesgo": "Falsos positivos del filtro anti-inyección que bloquean consultas legítimas",
        "probabilidad": 3,
        "impacto": 3,
        "mitigacion": (
            "Reglas de entrada calibradas con calificadores explícitos para permitir palabras "
            "académicas comunes ('instrucciones para calcular', 'contraseña del portal')."
        ),
        "evidencia": ["ataques:B-01", "ataques:B-02"],
        "estado": "verificada",
        "residual": 2,
        "limites": [],
        "nota": "",
        "supervision": "",
    },
    {
        "id": "R-08",
        "riesgo": "Indisponibilidad del proveedor externo o caída silenciosa sin aviso operativo",
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": (
            "`servicio/respaldo.py` devuelve HTTP 503 explícito por defecto si falta el modelo real "
            "y exige habilitar `PERMITIR_RESPALDO=1` para degradación controlada."
        ),
        "evidencia": ["pruebas:tests/parciales/test_respaldo.py"],
        "estado": "verificada",
        "residual": 3,
        "limites": [],
        "nota": "",
        "supervision": "",
    },
    {
        "id": "R-09",
        "riesgo": "Desviación de contratos entre componentes internos o entradas malformadas",
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": (
            "Guardias Pydantic (`exigir` con `Fragmento` en `extra='forbid'`) en cada frontera "
            "de `servicio/cadena.py` y validación estricta de rutas/body en FastAPI."
        ),
        "evidencia": ["pruebas:tests/parciales/test_contratos.py", "matriz:MP-05", "matriz:MP-07"],
        "estado": "verificada",
        "residual": 2,
        "limites": [],
        "nota": "",
        "supervision": "",
    },
]


def escribir_matriz(riesgos: list[dict[str, Any]] = RIESGOS) -> Path:
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    ordenados = sorted(riesgos, key=lambda r: (-int(r["residual"]), r["id"]))
    h = huella(riesgos)

    lineas = [
        "# Matriz de Riesgos con Mitigaciones Verificadas",
        "",
        f"- **Fecha de generación:** {fecha}",
        f"- **Huella de la matriz:** {h}",
        f"- **Riesgos evaluados:** {len(ordenados)}",
        "",
        "## Resumen ordenado por riesgo residual",
        "",
        "| ID | Riesgo | Inherente | Residual | Estado | Evidencias | Límites |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in ordenados:
        inh = inherente(r)
        res = int(r["residual"])
        evs = ", ".join(f"`{e}`" for e in r["evidencia"])
        lims = ", ".join(r["limites"]) if r["limites"] else "—"
        lineas.append(
            f"| {r['id']} | {r['riesgo']} | {inh} ({categoria(inh)}) | "
            f"{res} ({categoria(res)}) | {r['estado']} | {evs} | {lims} |"
        )

    lineas.extend(["", "## Detalle de mitigaciones, límites y supervisión humana", ""])
    for r in ordenados:
        inh = inherente(r)
        res = int(r["residual"])
        lineas.extend(
            [
                f"### {r['id']} — {r['riesgo']}",
                f"- **Puntaje:** inherente `{inh}` ({categoria(inh)}) → residual `{res}` ({categoria(res)})",
                f"- **Estado:** `{r['estado']}`",
                f"- **Mitigación:** {r['mitigacion']}",
                f"- **Evidencias:** {', '.join(f'`{e}`' for e in r['evidencia'])}",
            ]
        )
        if r.get("limites"):
            lineas.append(f"- **Límites cubiertos:** {', '.join(r['limites'])}")
            lineas.append(f"- **Nota técnica:** {r['nota']}")
        if r.get("supervision"):
            lineas.append(f"- **Supervisión humana obligatoria:** {r['supervision']}")
        lineas.append("")

    DESTINO.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return DESTINO


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera docs/matriz_riesgos.md desde riesgos.py.")
    parser.add_argument("--escribir", action="store_true", help="Escribe docs/matriz_riesgos.md.")
    args = parser.parse_args()

    ordenados = sorted(RIESGOS, key=lambda r: (-int(r["residual"]), r["id"]))
    print(f"Matriz de Riesgos ({len(ordenados)} riesgos, huella {huella(RIESGOS)}):")
    for r in ordenados:
        inh = inherente(r)
        res = int(r["residual"])
        print(
            f"  {r['id']} [{r['estado']:10s}] inh={inh:2d} ({categoria(inh):7s}) -> "
            f"res={res:2d} ({categoria(res):7s}) | {r['riesgo']}"
        )
    if args.escribir:
        ruta = escribir_matriz(RIESGOS)
        print(f"Matriz escrita en {ruta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
