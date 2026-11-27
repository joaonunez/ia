"""Grafo de supervisión humana (HITL) con LangGraph para despliegue de prompts (U2.7 · Bloque 32).

Flujo:
    START -> propose -> supervise (interrupt) -> apply -> END

Usa checkpointer (`InMemorySaver` por defecto; intercambiable por `SqliteSaver`
o Postgres en producción), `thread_id` único por despliegue y validación estricta
de booleano y estado pendiente al reanudar.
"""
from __future__ import annotations

import uuid
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from prompt_registry import PROMPT_NAME, build_project_registry


class DeploymentState(TypedDict):
    """Estado que viaja por el grafo de despliegue supervisado."""

    new_fingerprint: str
    approved: bool
    status: str


def new_thread_id(prefix: str = "despliegue") -> str:
    """Genera un thread_id único por solicitud de despliegue."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def propose_node(state: DeploymentState) -> dict[str, Any]:
    """Registra la propuesta de nueva huella de prompt antes de pedir aprobación."""
    return {"status": "propuesta"}


def supervise_node(state: DeploymentState) -> dict[str, Any]:
    """Pausa el grafo y exige una decisión humana explícita antes de activar."""
    decision = interrupt(
        {
            "motivo": "aprobar nueva version de prompt en produccion",
            "huella_propuesta": state["new_fingerprint"],
        }
    )
    if not isinstance(decision, bool):
        raise TypeError("La decisión de reanudación debe ser estrictamente bool.")
    return {"approved": decision}


def apply_node(state: DeploymentState) -> dict[str, Any]:
    """Activa o rechaza la versión propuesta según la decisión humana."""
    if state["approved"]:
        return {"status": "activada"}
    return {"status": "rechazada"}


def build_deployment_graph(checkpointer: Any = None):
    """Compila el grafo de despliegue supervisado con checkpointer."""
    graph = StateGraph(DeploymentState)
    graph.add_node("propose", propose_node)
    graph.add_node("supervise", supervise_node)
    graph.add_node("apply", apply_node)

    graph.add_edge(START, "propose")
    graph.add_edge("propose", "supervise")
    graph.add_edge("supervise", "apply")
    graph.add_edge("apply", END)

    return graph.compile(checkpointer=checkpointer or InMemorySaver())


def start_deployment(
    app: Any,
    new_fingerprint: str,
    thread_id: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Inicia un despliegue y devuelve `(config, resultado_interrumpido)`."""
    config = {"configurable": {"thread_id": thread_id or new_thread_id()}}
    result = app.invoke(
        {
            "new_fingerprint": new_fingerprint,
            "approved": False,
            "status": "iniciada",
        },
        config=config,
    )
    return config, result


def resolve_deployment(app: Any, config: dict[str, Any], approve: bool) -> dict[str, Any]:
    """Reanuda un despliegue pausado validando booleano estricto y estado pendiente."""
    if not isinstance(approve, bool):
        raise TypeError(
            "approve debe ser un booleano (True o False); no pases strings como 'no'."
        )
    snapshot = app.get_state(config)
    if not snapshot.next:
        raise ValueError(
            "No hay ninguna aprobación pendiente para este thread_id "
            "(ya fue resuelto o no existe)."
        )
    return app.invoke(Command(resume=approve), config=config)


def main() -> None:
    """Demuestra pausa (`__interrupt__`), aprobación y rechazo con thread_ids distintos."""
    registry = build_project_registry()
    latest = registry.latest(PROMPT_NAME)
    assert latest is not None
    fingerprint = latest["huella"]

    app = build_deployment_graph()

    # 1. Camino de aprobación
    config_approve, paused = start_deployment(app, fingerprint)
    snapshot = app.get_state(config_approve)
    print("1) tras invocar (pausado):", paused)
    print("2) pendiente:", snapshot.interrupts[0].value)
    approved_result = resolve_deployment(app, config_approve, approve=True)
    print("3) tras aprobar:", approved_result)

    # 2. Camino de rechazo (con thread_id nuevo)
    config_reject, _ = start_deployment(app, fingerprint)
    rejected_result = resolve_deployment(app, config_reject, approve=False)
    print("4) tras rechazar:", rejected_result)


if __name__ == "__main__":
    main()
