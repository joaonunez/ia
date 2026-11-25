# Agentes, herramientas y memoria (U2.4)

Apuntes de la Unidad 2.4 (Bloques 21 a 23), aplicados al asistente del gestor académico. El código está en [`src/agent.py`](../src/agent.py) y [`src/supervision.py`](../src/supervision.py); los límites del agente, en [`agent-autonomy-limits.md`](agent-autonomy-limits.md). La chain de la unidad anterior está en [`orchestration.md`](orchestration.md).

## Chain contra agente

| | Chain (U2.3) | Agente (U2.4) |
| --- | --- | --- |
| Quién escribe el camino | Tú, de antemano | El modelo, en tiempo de ejecución |
| Número de pasos | Fijo | Varía con la entrada |
| Llamadas al modelo | Se conocen antes (3 en `routing.py`) | Un mínimo de 2 con herramienta; no se sabe el máximo |
| Costo y latencia | Predecibles | Un rango |
| Dónde puede fallar | En tu diseño | En tu diseño y en lo que el modelo decida |
| Cómo se prueba | Mockeando cada pieza | Mirando las decisiones, además del código |

Un agente conviene cuando el camino depende de la entrada de formas que no se pueden enumerar. Si el camino es siempre el mismo, o son pocos caminos conocidos, una chain (incluso bifurcada) es más rápida, más barata y más fácil de probar. En este proyecto las dos conviven: `routing.py` resuelve consultas con contexto ya entregado; `agent.py` decide qué dato ir a buscar.

## El ciclo ReAct

Razonar, actuar, observar, repetir hasta tener con qué responder. Cada vuelta es una llamada al modelo.

```text
Consulta:    ¿Y cuántos días de inasistencia tiene?   (la sesión ya habló de Diego Soto)
Acción:      get_attendance(student_name="Diego Soto", include_absences=True)
Observación: Diego Soto tiene 72% de asistencia (11 días de inasistencia).
Respuesta:   Diego Soto tiene 11 días de inasistencia (72% de asistencia).
```

Esa traza salió de la corrida real. Con `verbose=True` se ve por consola; con `return_intermediate_steps=True` queda en `result["intermediate_steps"]`, una lista de pares (acción, observación).

## Herramientas

Una herramienta es una función de Python con un nombre y una descripción que el modelo lee para decidir cuándo usarla.

- **El docstring es la descripción.** Debe decir cuándo conviene la herramienta, no cómo está hecha por dentro. Una vaga hace que el agente elija mal; una demasiado amplia «atrae» consultas que no le corresponden.
- **Con más de un parámetro, `args_schema`.** Una clase Pydantic con un `Field(description=...)` por argumento le dice al modelo qué es cada uno y valida los tipos antes de ejecutar: pasar `include_absences="tal vez"` lanza `ValidationError` y la función ni se llama (`test_args_schema_rejects_a_value_of_the_wrong_type`).
- **El nombre explícito** (`@tool("get_grades", ...)`) es el que aparece en la traza, no el de la función.
- **Devolver siempre texto y atrapar los errores adentro.** Una excepción corta el ciclo; un texto como «No se encontró un estudiante…» le deja al agente algo con qué razonar.
- **Con un solo parámetro simple no hace falta `args_schema`:** un tipo anotado y un buen docstring bastan.

| Herramienta | Qué hace | Riesgo |
| --- | --- | --- |
| `get_grades` | Promedio de un estudiante | Bajo |
| `get_attendance` | Asistencia y, opcional, inasistencias | Bajo |
| `send_guardian_notice` | Aviso al apoderado (simulado) | Alto |

## Memoria entre interacciones

Cada `invoke()` de un `AgentExecutor` empieza de cero. `RunnableWithMessageHistory` le agrega un historial por `session_id` que se reinyecta en cada llamada.

- El prompt necesita **dos** `MessagesPlaceholder`: `chat_history` (lo dicho antes, va antes del mensaje humano) y `agent_scratchpad` (el razonamiento de la consulta actual, va después).
- Las claves del envoltorio tienen que coincidir con el prompt: `input_messages_key="input"` y `history_messages_key="chat_history"`. Si `input_messages_key` no coincide, el agente responde normal pero el historial queda vacío en silencio. Se comprueba mirando que `len(historial.messages)` crezca (`test_two_sessions_do_not_share_history`).
- **Dos sesiones no comparten historial**, y verificarlo no es opcional en un agente que atiende a más de una persona: lo contrario filtraría datos de un usuario a otro.
- **Cada turno cuesta más que el anterior:** el turno N reenvía los N-1 anteriores completos.
- La memoria es sobre la conversación, no sobre los datos del negocio, y no persiste sola: este historial vive en memoria y se pierde al reiniciar.

## Autonomía y supervisión humana

Autonomía es cuánto puede hacer el agente sin que nadie intervenga. Se clasifica cada herramienta por lo que pasa si el agente se equivoca:

| Riesgo | Ejemplo | Qué se hace |
| --- | --- | --- |
| Bajo: solo lectura | Consultar notas | Se ejecuta directo; se revisa después en la traza |
| Medio: escritura reversible | Guardar una nota | Directo, con registro |
| Alto: irreversible o con impacto | Avisar a un apoderado | Aprobación humana antes de ejecutar |

Reglas que se aplicaron:

1. La aprobación se reserva para lo de riesgo alto. Pedirla siempre hace que quien aprueba deje de leer.
2. **El valor por defecto es «no aprobado»:** sin respuesta a tiempo, no se ejecuta.
3. La decisión se registra siempre, se apruebe o no.
4. Un tope de iteraciones (`MAX_ITERATIONS = 5`) corta a un agente que no converge.

## Trazas

`verbose=True` se pierde al cerrar la consola. `record_trace` guarda cada interacción como una línea JSON con la consulta, las herramientas usadas con sus argumentos y la respuesta final, para revisarla después. Se revisa una muestra con regularidad y **todas** las trazas de herramientas de riesgo alto. `flag_repeated_tools` hace una primera pasada automática (la misma herramienta dos veces seguidas), pero la decisión de si algo está mal sigue siendo humana. Una traza es como el registro de vuelo: no evita el problema, permite entenderlo después.

## Lo que costó aprender en la práctica

- **`AgentExecutor` y `create_tool_calling_agent` viven en `langchain-classic`** desde LangChain 1.x: `from langchain_classic.agents import ...`. Con `langchain.agents` el import falla.
- **`select()` sobre `stdin` no funciona en Windows.** La lección lo usa para el timeout de la aprobación; aquí se reemplazó por un hilo con `join(timeout)`. El hilo queda esperando si nadie responde (es demonio y no impide cerrar el programa).
- **Gemini devuelve el contenido como lista de bloques**, no como string. Sin pasarlo por `content_to_text`, el historial se rompe en el segundo turno. Las pruebas con modelo falso no lo veían; la corrida real sí.
- **El modelo falso de LangChain (`GenericFakeChatModel`) no sabe hacer streaming de una llamada a herramienta sin texto.** Las pruebas lo usan con `disable_streaming=True` y un `bind_tools` que devuelve el mismo modelo.
- **`RunnableWithMessageHistory` aparece como obsoleto** en LangChain 1.x. Sigue funcionando, genera avisos en las pruebas y su reemplazo oficial es la persistencia de LangGraph.
- **La respuesta final puede contradecir una observación.** La herramienta dijo «simulado» y el agente respondió «He enviado un aviso». Por eso se revisan las trazas, no solo las respuestas.

## Nombres de la lección y del repo

| Lección | Repo |
| --- | --- |
| `agente_con_herramientas.py` | `src/agent.py` |
| `limites_autonomia_agente.md` | `docs/agent-autonomy-limits.md` |
| `esperar_aprobacion` | `wait_for_approval` |
| `registrar_aprobacion` | `record_approval` |
| `registrar_traza` | `record_trace` |
| `marcar_repeticiones_sospechosas` | `flag_repeated_tools` |
| `trazas_agente.jsonl` | `docs/agent-traces.jsonl` |
| `consultar_estado_envio_detallado`, `calcular_costo_envio`, `generar_reembolso` (ejemplos de envíos) | `get_attendance`, `get_grades`, `send_guardian_notice` (dominio del gestor académico) |
| `entrada` / `session_id` / `acciones` | `input` / `session_id` / `actions` |
