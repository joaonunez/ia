"""Matriz de riesgos de IA generativa y análisis de frontera (U2.7 · Bloque 32).

Evalúa riesgos concretos del asistente académico de solo lectura con:
- `puntaje = probabilidad * impacto` (escala 1..5 x 1..5)
- cortes: CRITICO >= 15, ALTO >= 9, MEDIO >= 4, BAJO < 4
- análisis de sensibilidad en frontera (`±1`)
- verificación de gobernanza: todo ALTO/CRITICO exige punto de supervisión concreto.
"""
from __future__ import annotations

from typing import Any

PROJECT_RISKS: list[dict[str, Any]] = [
    {
        "riesgo": (
            "Inyección de prompt indirecta incrustada en un reglamento o comentario "
            "indexado en Chroma que intenta filtrar instrucciones internas o cambiar el rol"
        ),
        "probabilidad": 4,
        "impacto": 4,
        "mitigacion": (
            "Defensa en 3 capas: separación SystemMessage/HumanMessage, delimitadores "
            "<contexto_referencia> y filtro determinista previo en "
            "src/observability_security.py (Bloque 31)"
        ),
        "punto_supervision": (
            "Revisión humana por el encargado técnico antes de re-indexar o aprobar "
            "cualquier documento que el filtro de inyección haya descartado"
        ),
    },
    {
        "riesgo": (
            "Alucinación de cifras escolares (porcentaje de asistencia o nota mínima) "
            "cuando el corpus RAG no contiene la norma consultada"
        ),
        "probabilidad": 3,
        "impacto": 4,
        "mitigacion": (
            "Prompt estricto con citas numeradas [1] y regla explícita de admitir falta "
            "de contexto + evaluación de precisión/recall/F1 en src/rag_pipeline.py y "
            "src/rag_evaluator.py (Bloques 26 y 27)"
        ),
        "punto_supervision": (
            "Verificación semanal de respuestas sin cita o con rechazo por el equipo "
            "académico antes de cerrar cambios de prompt o de corpus"
        ),
    },
    {
        "riesgo": (
            "Envío no autorizado de un aviso a un apoderado por error de interpretación "
            "del agente con herramientas"
        ),
        "probabilidad": 2,
        "impacto": 5,
        "mitigacion": (
            "Compuerta de aprobación humana explícita y traza JSONL auditada en "
            "src/supervision.py y docs/agent-autonomy-limits.md (Bloque 23)"
        ),
        "punto_supervision": (
            "Confirmación humana obligatoria (s/n o botón de aprobación) antes de "
            "ejecutar cualquier acción externa hacia apoderados"
        ),
    },
    {
        "riesgo": (
            "Despliegue silencioso de una modificación defectuosa del prompt de sistema "
            "que degrada citas o desactiva defensas anti-inyección"
        ),
        "probabilidad": 2,
        "impacto": 4,
        "mitigacion": (
            "Versionado con huella SHA-256 + diff unificado en src/prompt_registry.py "
            "y flujo de aprobación con interrupt() en src/supervision_graph.py (Bloque 32)"
        ),
        "punto_supervision": (
            "Aprobación explícita de un revisor sobre el diff de prompt antes de "
            "activar la nueva huella en producción"
        ),
    },
    {
        "riesgo": (
            "Agotamiento de cuota o picos de costo/latencia por aumento excesivo de k "
            "o bucles de reintento ante errores 429 del proveedor"
        ),
        "probabilidad": 2,
        "impacto": 3,
        "mitigacion": (
            "Backoff exponencial con jitter, máximo 3 intentos y registro de costo por "
            "operación en src/client.py (Bloques 12 y 13) + benchmark k=3 vs k=6 en "
            "src/rag_pipeline.py (Bloque 28)"
        ),
        "punto_supervision": (
            "Revisión mensual del consumo acumulado en JSONL y ajuste de k o presupuesto"
        ),
    },
    {
        "riesgo": (
            "Exposición accidental de preguntas con PII o llaves de API en logs de "
            "depuración del servicio"
        ),
        "probabilidad": 1,
        "impacto": 3,
        "mitigacion": (
            "Logging JSON que registra solo longitud y huella SHA-256 corta en "
            "src/observability_security.py (Bloque 31) y exclusión de .env en .gitignore (Bloque 4)"
        ),
        "punto_supervision": (
            "Revisión puntual en PRs que agreguen nuevos campos al logger estructurado"
        ),
    },
]


def _validate_scale(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not (1 <= value <= 5):
        raise ValueError(f"{field_name} debe ser un entero entre 1 y 5, recibido: {value!r}")
    return value


def risk_score(probability: int, impact: int) -> int:
    """Calcula el puntaje de riesgo (1..25) validando la escala 1..5."""
    p = _validate_scale(probability, "probabilidad")
    i = _validate_scale(impact, "impacto")
    return p * i


def risk_category(score: int) -> str:
    """Clasifica el puntaje en CRITICO (>=15), ALTO (>=9), MEDIO (>=4) o BAJO (<4)."""
    if score >= 15:
        return "CRITICO"
    if score >= 9:
        return "ALTO"
    if score >= 4:
        return "MEDIO"
    return "BAJO"


def is_at_boundary(probability: int, impact: int) -> bool:
    """Indica si variar probabilidad o impacto en ±1 (dentro de 1..5) cambia la categoría."""
    p = _validate_scale(probability, "probabilidad")
    i = _validate_scale(impact, "impacto")
    current = risk_category(risk_score(p, i))
    neighbors = [(p + 1, i), (p - 1, i), (p, i + 1), (p, i - 1)]
    for p2, i2 in neighbors:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if risk_category(risk_score(p2, i2)) != current:
            return True
    return False


def evaluate_risk_matrix(risks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Evalúa puntaje, categoría y frontera de cada riesgo y ordena de mayor a menor."""
    source = PROJECT_RISKS if risks is None else risks
    evaluated: list[dict[str, Any]] = []
    for item in source:
        score = risk_score(item["probabilidad"], item["impacto"])
        category = risk_category(score)
        boundary = is_at_boundary(item["probabilidad"], item["impacto"])
        evaluated.append(
            {
                **item,
                "puntaje": score,
                "categoria": category,
                "al_limite": boundary,
            }
        )
    return sorted(evaluated, key=lambda row: (-row["puntaje"], row["riesgo"]))


def validate_risk_matrix(evaluated: list[dict[str, Any]]) -> list[str]:
    """Verifica las reglas mínimas del Bloque 32 y devuelve lista de problemas (vacía si ok)."""
    errors: list[str] = []
    if len(evaluated) < 5:
        errors.append(f"Se requieren al menos 5 riesgos; hay {len(evaluated)}.")

    high_or_critical = [r for r in evaluated if r["categoria"] in {"ALTO", "CRITICO"}]
    if not high_or_critical:
        errors.append("Debe existir al menos un riesgo ALTO o CRITICO.")

    for row in high_or_critical:
        supervision = str(row.get("punto_supervision") or "").strip()
        if len(supervision) < 15:
            errors.append(
                f"Riesgo {row['categoria']} sin punto de supervisión concreto: {row['riesgo']}"
            )

    block_refs = [
        r for r in evaluated if "bloque" in str(r.get("mitigacion") or "").lower()
    ]
    if len(block_refs) < 2:
        errors.append(
            "Al menos dos mitigaciones deben apuntar a controles construidos con número de bloque."
        )

    return errors


def main() -> None:
    """Imprime la matriz ordenada, los riesgos en frontera y la validación."""
    evaluated = evaluate_risk_matrix()
    for row in evaluated:
        tag = " [AL LIMITE]" if row["al_limite"] else ""
        print(f"{row['categoria']:8} ({row['puntaje']:2}){tag} - {row['riesgo']}")

    print("\nRiesgos en frontera (revisar con otra persona):")
    for row in evaluated:
        if row["al_limite"]:
            print(" -", row["riesgo"])

    issues = validate_risk_matrix(evaluated)
    print("\nValidación:", "OK (0 problemas)" if not issues else f"FALLOS: {issues}")


if __name__ == "__main__":
    main()
