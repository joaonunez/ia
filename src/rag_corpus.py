"""Corpus reglamentario y técnico propio del asistente académico (sin dependencias pesadas)."""
from __future__ import annotations

# Corpus propio de 8 documentos breves y coherentes sobre el asistente del
# gestor académico y el reglamento escolar ficticio del proyecto.
CORPUS: list[dict[str, str]] = [
    {
        "id": "doc0",
        "fuente": "reglamento_asistencia.md",
        "fecha": "2026-11-25",
        "tema": "asistencia",
        "contenido": (
            "El porcentaje mínimo de asistencia para promoción escolar es del 85 %. "
            "Cuando un estudiante baja del 80 % o acumula más de 8 días de inasistencia "
            "en el trimestre, el gestor académico debe revisar el caso y coordinar "
            "un contacto preventivo con el apoderado."
        ),
    },
    {
        "id": "doc1",
        "fuente": "reglamento_notas.md",
        "fecha": "2026-11-25",
        "tema": "calificaciones",
        "contenido": (
            "La escala de calificaciones chilena va de 1.0 a 7.0, con nota mínima de "
            "aprobación 4.0. Un promedio bajo 4.0 en asignaturas troncales activa una "
            "alerta académica que el gestor debe registrar antes del cierre del período."
        ),
    },
    {
        "id": "doc2",
        "fuente": "protocolo_apoderados.md",
        "fecha": "2026-11-25",
        "tema": "comunicaciones",
        "contenido": (
            "Todo aviso formal enviado al apoderado por riesgo de repitencia o baja "
            "asistencia requiere aprobación humana explícita antes de despacharse. "
            "El mensaje enviado no se puede retirar y queda auditado con fecha y motivo."
        ),
    },
    {
        "id": "doc3",
        "fuente": "cliente_reintentos.md",
        "fecha": "2026-11-25",
        "tema": "resiliencia",
        "contenido": (
            "El cliente HTTP del asistente reintenta hasta 3 veces ante errores 429, "
            "5xx o cortes de red, aplicando espera exponencial (2, 4 y 8 segundos, "
            "tope 30 s) con jitter del 10 %. Los errores 401 y 403 nunca se reintentan "
            "y fallan de inmediato con ValueError."
        ),
    },
    {
        "id": "doc4",
        "fuente": "decision_modelo_costos.md",
        "fecha": "2026-11-25",
        "tema": "costos",
        "contenido": (
            "El modelo elegido para generación es gemini-3.5-flash-lite por su baja "
            "latencia y bajo costo: USD 0.30 por millón de tokens de entrada y "
            "USD 2.50 por millón de tokens de salida. El costo de sesión solo suma "
            "respuestas válidas."
        ),
    },
    {
        "id": "doc5",
        "fuente": "arquitectura_solo_lectura.md",
        "fecha": "2026-11-25",
        "tema": "arquitectura",
        "contenido": (
            "En producción sobre la intranet escolar, el asistente consulta datos "
            "académicos con un rol de base de datos de solo lectura (intranet_ai_ro). "
            "No puede crear, modificar ni eliminar registros oficiales de estudiantes."
        ),
    },
    {
        "id": "doc6",
        "fuente": "limites_autonomia.md",
        "fecha": "2026-11-25",
        "tema": "gobernanza",
        "contenido": (
            "El agente limita su ciclo razonar-actuar a un máximo de 5 iteraciones "
            "(MAX_ITERATIONS = 5) para evitar bucles costosos. Cada interacción queda "
            "registrada en agent-traces.jsonl y cada decisión de aprobación en "
            "agent-approvals.jsonl."
        ),
    },
    {
        "id": "doc7",
        "fuente": "estrategia_pruebas.md",
        "fecha": "2026-11-25",
        "tema": "calidad",
        "contenido": (
            "Las pruebas unitarias del repositorio usan mocks y embeddings deterministas "
            "para verificar lógica, reintentos, métricas y citas sin gastar cuota ni "
            "depender de la red; la suite completa corre en pocos segundos."
        ),
    },
]
