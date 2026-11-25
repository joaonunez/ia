# Límites de autonomía: asistente del gestor académico

Cierra la Unidad 2.4 (Bloque 23). Describe el agente que está en [`src/agent.py`](../src/agent.py), con la supervisión y las trazas de [`src/supervision.py`](../src/supervision.py), no un agente ideal. Cada afirmación se puede comprobar en el código, en [`tests/test_agent.py`](../tests/test_agent.py) o en las trazas reales de [`agent-traces.jsonl`](agent-traces.jsonl) y [`agent-approvals.jsonl`](agent-approvals.jsonl).

## Herramientas y nivel de riesgo

- `get_grades`: **bajo**. Solo lee el promedio de un estudiante. Si el agente la usa de más o con un nombre equivocado, el peor resultado es una respuesta incorrecta; no modifica nada.
- `get_attendance`: **bajo**. Solo lee el porcentaje de asistencia y, si se pide, los días de inasistencia. Mismo peor caso que la anterior.
- `send_guardian_notice`: **alto**. Avisa al apoderado de un estudiante, y un aviso enviado no se puede retirar. Un error aquí le llega a una familia: un aviso equivocado sobre un menor, con un motivo mal redactado o al estudiante incorrecto. Es la única herramienta que escribe.

No hay herramientas de riesgo medio: el agente no guarda notas ni preferencias.

El aviso está **simulado**: la función devuelve «Aviso enviado (simulado)» y no se conecta con ninguna intranet. Existe para ejercitar el mecanismo de supervisión con una acción que justifique pedirla. Un asistente de solo lectura (decisión de [`decision-arquitectura.md`](decision-arquitectura.md)) no necesita esta herramienta; si el proyecto vuelve a ser solo lectura, se quita de `build_tools` y las otras dos siguen intactas.

## Herramientas que requieren aprobación humana

- `send_guardian_notice`: es la única de riesgo alto, así que es la única con aprobación. Las dos de solo lectura no la piden a propósito: pedir confirmación por cada consulta de notas haría que quien aprueba dejara de leer lo que aprueba.

Cómo funciona (verificado contra el código):

- La herramienta llama a `approve(...)` antes de actuar ([`agent.py:151`](../src/agent.py)). Por defecto `approve` es `wait_for_approval` ([`supervision.py:24`](../src/supervision.py)).
- `wait_for_approval` solo aprueba con una respuesta «s». Cualquier otra respuesta, un timeout (300 s por defecto) o la falta de entrada estándar cuentan como **no aprobado**: el valor por defecto es el seguro.
- Si el estudiante no existe, la herramienta responde sin pedir aprobación: no hay nada que aprobar.
- La decisión se guarda siempre, se apruebe o no, en `agent-approvals.jsonl` (herramienta, argumentos, resultado y hora).
- Funciona en Windows. La lección usa `select()` sobre `stdin`, que ahí no sirve; esta versión espera con un hilo.

Pruebas: `test_notice_is_sent_only_after_approval_and_the_decision_is_recorded`, `test_notice_is_not_sent_when_the_supervisor_rejects_it`, `test_unknown_student_never_asks_for_approval`, `test_agent_does_not_send_a_notice_the_supervisor_rejected`, y en `test_supervision.py` las de timeout y de falta de entrada estándar.

Otros límites de autonomía que ya están en el código:

- **Tope de vueltas:** `MAX_ITERATIONS = 5`. Un agente que no converge se corta en vez de seguir llamando al modelo (`test_agent_stops_after_the_iteration_limit`).
- **Tiempo:** el modelo se crea con `timeout=20` y `max_retries=2`.
- **Qué puede hacer:** solo las tres herramientas; el prompt dice que el aviso se envía únicamente si la persona lo pide de forma explícita.

## Revisión de trazas

- **Qué se guarda:** `record_trace` escribe una línea por interacción en `agent-traces.jsonl`: sesión, consulta, herramientas con sus argumentos y observaciones, y respuesta final. Lo llama `ask_agent` después de cada consulta.
- **Frecuencia:** una muestra pequeña cada semana, y **todas** las trazas donde aparezca `send_guardian_notice` (en las 8 trazas de ejemplo, 2).
- **Qué se busca:**
  1. La misma herramienta dos veces seguidas. `flag_repeated_tools()` hace esa primera pasada y devuelve las sesiones candidatas. Compara solo el nombre de la herramienta, no los argumentos, así que puede marcar casos legítimos (dos consultas distintas a `get_grades`).
  2. `send_guardian_notice` sin una línea correspondiente en `agent-approvals.jsonl`: indicaría que la aprobación se saltó.
  3. Una respuesta final que afirma algo que ninguna observación respalda. No hay revisión automática de esto; es lectura humana.

Qué mostraron las 8 trazas reales (corridas del 2026-11-12, `gemini-3.5-flash-lite`, datos ficticios):

| Consulta | Herramienta elegida |
| --- | --- |
| ¿Qué promedio tiene Diego Soto? | `get_grades` |
| ¿Y cuántos días de inasistencia tiene? | `get_attendance` con `include_absences=True`; el agente resolvió «tiene» como Diego Soto por la memoria |
| Avisa al apoderado de Diego Soto… | `send_guardian_notice`, con aprobación pedida |
| ¿Cómo se llama el director? | ninguna (`actions` vacío); respondió que no tiene ese dato |

`flag_repeated_tools()` no marcó nada.

**Cómo se hicieron esas corridas:** `python src/agent.py` dos veces, respondiendo la aprobación por entrada estándar: una vez `s` y otra `n`. Quien aprobó fue un guion, no una persona supervisora. Sirven para ver que el mecanismo funciona; no demuestran que una persona real lo use bien.

Lo que revelaron y no esperaba:

- **La respuesta final puede ocultar que el aviso es simulado.** En la corrida aprobada, la herramienta devolvió «Aviso enviado (simulado)», pero el agente respondió «He enviado un aviso al apoderado». La observación y la respuesta final no coinciden en ese detalle. Es el patrón 3 de arriba, visto en la práctica.
- **Gemini devuelve el contenido como lista de bloques** (texto más una firma), no como string. Sin normalizarlo, el historial se rompía en el segundo turno. Lo detectó la corrida real, no las pruebas con modelo falso; `content_to_text` lo corrige y `test_memory_survives_a_model_that_answers_with_content_blocks` lo cubre.

## Qué hacer ante un comportamiento inesperado

En este orden:

1. **Si hay un aviso enviado por error:** no hay forma de retirarlo desde el agente. Contactar a la familia desde el canal normal del colegio y anotar el caso. Por eso la herramienta exige aprobación.
2. **Cortar la herramienta:** quitar `send_guardian_notice` de la lista que devuelve `build_tools`. El agente deja de poder usarla en el siguiente arranque; las de lectura siguen funcionando.
3. **Mirar la traza de la sesión afectada** en `agent-traces.jsonl` y su línea en `agent-approvals.jsonl`: qué herramienta se eligió, con qué argumentos y qué observación recibió el agente.
4. **Corregir la causa según lo que muestre la traza:**
   - Elige una herramienta que no corresponde: reescribir el docstring de esa herramienta pensando en qué pregunta debe dispararla.
   - Se repite sin avanzar: revisar si la observación es ambigua; bajar `MAX_ITERATIONS` si hace falta.
   - La respuesta final contradice la observación: endurecer el prompt del agente y, si persiste, hacer que la herramienta devuelva el texto exacto que debe mostrarse.
5. **Agregar una prueba** que reproduzca el caso antes de dar el cambio por bueno, como se hizo con el contenido en bloques.

## Lo que todavía no está resuelto

- La aprobación llega por la consola. En un uso real debería venir de un panel que una persona revise, con identidad: hoy el registro dice que se aprobó, no quién.
- El historial de conversación vive en memoria y se pierde al reiniciar. `RunnableWithMessageHistory` aparece como obsoleto en LangChain 1.x y sigue funcionando; la alternativa oficial es la persistencia de LangGraph.
- Las trazas y las aprobaciones son archivos de texto sin control de acceso. En un uso real contendrían nombres y notas de menores: hay que restringir quién las lee y por cuánto tiempo se guardan.
- Cada consulta puede costar varias llamadas al modelo y no hay un tope de costo por sesión.
- No hay autenticación por usuario: cualquiera que invoque el agente puede pedir el aviso (la aprobación humana es la única barrera).
