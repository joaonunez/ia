# Asistente Académico IA — Proyecto Gradual de Joao Nunez (Accenture / Skillnest)

Repositorio: https://github.com/joaonunez/ia

Asistente IA de **solo lectura** para el gestor académico de una intranet escolar: responde consultas reglamentarias con citas verificables, defensa en profundidad contra inyección/alucinaciones y datos simulados de estudiantes, compuesto en Docker Compose con una API FastAPI y una interfaz web mínima.

## Requisitos

- Docker con Compose (`docker compose version`).
- Puertos `8000` (API) y `8080` (interfaz web) libres en tu equipo.
- Python `3.11` (misma versión que `Dockerfile`: `python:3.11-slim`) para ejecutar pruebas y verificadores locales.

## Instalación

Ejecuta todos los comandos desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate      # Linux / macOS
# En Windows PowerShell:
# Set-ExecutionPolicy -Scope Process RemoteSigned
# .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## Configuración

1. Copia la plantilla de variables de entorno:
   ```bash
   cp .env.example .env
   ```
2. Completa `.env` según necesites (`.env` está excluido en `.gitignore` y nunca se sube a git):
   - `GEMINI_API_KEY` (secreto, opcional): clave de API de Gemini. Si queda vacía, el servicio arranca en modo simulado local y `/health` informa `"modelo": "sin clave"`.
   - `API_KEY` (secreto, opcional): alias de compatibilidad para los scripts del Módulo 2 (`src/routing.py`, `src/agent.py`, `src/rag_pipeline.py`).
   - `ENTORNO` (configuración, opcional): `desarrollo` o `produccion` (por omisión `desarrollo`).
   - `MODELO` (configuración, opcional): `simulado` (por omisión) o `real`.
   - `PERMITIR_RESPALDO` (configuración, opcional): `0` (por omisión, falla con `503` si el modelo real no está disponible) o `1` (activa `ModeloRespaldo`, ver `docs/respaldos.md`).

## Cómo arrancar

### Con Docker Compose (recomendado)

```bash
docker compose up -d --build
```

### Sin Docker (desarrollo local)

```bash
python -m uvicorn servicio.main:app --host 127.0.0.1 --port 8000
```

Cuando termine, la solución queda disponible en:
- API FastAPI y OpenAPI: http://127.0.0.1:8000/docs (salud en http://127.0.0.1:8000/health; referencia generada en `docs/api.md`)
- Interfaz web: http://127.0.0.1:8080 (salud en http://127.0.0.1:8080/health)

## Cómo comprobar que funciona

1. Confirma que ambos servicios están sanos:
   ```bash
   docker compose ps
   ```
   Debes ver `api` e `interfaz` en estado `healthy`.
2. Abre http://127.0.0.1:8080, escribe `¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?` y pulsa **Preguntar**: debe responder con `85 %` y la fuente `"reglamento_asistencia.md"` (del corpus en `src/rag_corpus.py`).
3. Ejecuta los verificadores automáticos desde la raíz del repositorio:
   - `python verificar_dockerfile.py` y `python verificar_dockerfile.py interfaz/Dockerfile` → `7 de 7 reglas cumplidas`.
   - `python buscar_secretos.py` → `5 de 5 comprobaciones cumplidas`.
   - `python verificar_stack.py` → `7 de 7 comprobaciones cumplidas` (levanta, prueba los 16 casos y apaga).
   - `python verificar_entrega.py` → `7 de 7 comprobaciones cumplidas`.

## Pruebas

Suite automatizada sin red ni credenciales externas:

- Suite completa: `python -m pytest -q`
- Matriz QA y seguridad: `python verificar_matriz.py`, `python verificar_mitigaciones.py`, `python verificar_riesgos.py`
- Documentación y transferencia: `python verificar_readme.py`, `python generar_api_md.py --comprobar`, `python verificar_transferencia.py`, `python verificar_decisiones.py`, `python probar_en_frio.py`

## Decisiones

Las decisiones de arquitectura vigentes (`D-01`, `D-02`, `D-03`, `D-04`, `D-05`, `D-06`) se documentan con contexto, alternativas descartadas y costo en `docs/decisiones.md`:

- `D-01` (RAG de solo lectura sobre datos simulados), `D-02` (falla honesta HTTP 503 sin modelo real), `D-03` (cadena de 4 componentes con contratos Pydantic), `D-04` (defensa en profundidad), `D-05` (FastAPI + Docker Compose en dos servicios) y `D-06` (modelo objetivo `gemini-3.5-flash-lite`).

## Limitaciones

Todas las limitaciones técnicas verificadas (`LIM-01`, `LIM-02`, `LIM-03`, `LIM-04`) están trazadas contra su origen en código y su riesgo en `docs/limitaciones.md` y `docs/matriz_riesgos.md`:

- `LIM-01` (`MP-08` / `R-06`): recuperación léxica en modo simulado no resuelve sinónimos puros; en producción con `USE_LIVE_RAG=true` se mitiga con Chroma.
- `LIM-02` (`A-07` / `R-01`): evasión léxica con guiones intercalados supera el filtro inicial; contenida por limpieza de salida y solo lectura.
- `LIM-03` (`H-04` / `R-03`) y `LIM-04` (`H-05` / `R-03`): afirmaciones cualitativas agregadas y cifras en letras requieren supervisión humana del gestor académico.

## Estructura

- `servicio/`: API FastAPI (`servicio/main.py`, `servicio/cadena.py`, `servicio/logica.py`, `servicio/seguridad.py`, `servicio/fundamentacion.py`, `servicio/contratos.py`, `servicio/respaldo.py`, `servicio/errores.py`).
- `interfaz/`: cliente web ligero (`interfaz/main.py`, `interfaz/Dockerfile`).
- `docs/`: ficha funcional (`docs/ficha_diseno_funcional.md`), referencia API (`docs/api.md`), decisiones (`docs/decisiones.md`), limitaciones (`docs/limitaciones.md`), matrices (`docs/matriz_pruebas.md`, `docs/matriz_riesgos.md`), transferencia (`docs/prueba_transferencia.md`) y diario (`docs/diario_de_friccion.md`).
- `tests/`: pruebas unitarias y parciales en `tests/parciales/`.

## Cómo detener

```bash
docker compose down
```

Detiene y elimina los contenedores y la red del proyecto sin borrar las imágenes construidas.

## Problemas frecuentes

- **`Bind for 0.0.0.0:8000 failed: port is already allocated`**: otro proceso o contenedor usa el puerto `8000` (u `8080`). Detenlo o cambia el puerto izquierdo en `compose.yaml`.
- **`/health` muestra `"modelo": "sin clave"`**: comportamiento esperado si no definiste `GEMINI_API_KEY` en `.env`. Si la agregaste, recrea el contenedor con `docker compose up -d`.
- **La interfaz devuelve `502`**: no logra contactar a `api` en `http://api:8000`. Revisa `docker compose logs api`.
- **Error al conectar al motor de Docker en Windows**: abre **Docker Desktop** y espera a que `docker ps` responda sin error.

## Verificación cruzada

El registro de revisión del despliegue con criterios `VC-1` a `VC-6` y hallazgos está en `docs/verificacion_cruzada.md`.

## Avance por unidad

| Unidad | Fecha | Qué | Dónde |
| --- | --- | --- | --- |
| U1.2–U1.5 | 2026-10-16..22 | Cliente inicial, comparación de modelos y banco de prompts | `src/gemini_api.py`, `docs/decision-arquitectura.md`, `src/compare_models.py` |
| U2.1–U2.4 | 2026-10-28..11-12 | Cliente con reintentos, pipeline NLP, chains LangChain y agente con memoria y supervisión | `src/client.py`, `src/text_pipeline.py`, `src/routing.py`, `src/agent.py`, `src/supervision.py` |
| U2.5–U2.8 | 2026-11-25..27 | RAG Chroma con citas, personalización PEFT, observabilidad/seguridad, matriz de riesgos y Gate 2 | `src/rag_indexer.py`, `src/rag_pipeline.py`, `src/observability_security.py`, `docs/matriz-riesgos.md`, `docs/ensayo-gate2.md` |
| U3.1 | 2026-11-27 | Ficha de Diseño Funcional (5 secciones), diagrama PNG y verificadores | `docs/ficha_diseno_funcional.md`, `docs/diagrama_arquitectura.png`, `docs/revision_alcance.md`, `verificar_ficha_completa.py` |
| U3.2 | 2026-11-28 | Servicio FastAPI (`servicio/`), validación, errores unificados, cliente externo `httpx2` y evidencia HTTP | `verificar_servicio.py`, `casos.py`, `cliente_externo.py`, `registrar_pruebas.py`, `docs/registro_pruebas.md` |
| U3.3 | 2026-11-28 | Dockerfiles endurecidos, composición `compose.yaml` (`api` + `interfaz`), secretos y verificación cruzada | `compose.yaml`, `interfaz/main.py`, `verificar_dockerfile.py`, `verificar_imagen.py`, `buscar_secretos.py`, `verificar_stack.py`, `verificar_entrega.py`, `docs/verificacion_cruzada.md` |
| U3.4 | 2026-11-28 | Pruebas parciales con guardias de contrato, escenarios E2E, bitácora de ajustes, respaldo explícito `503` y registro verificable | `servicio/cadena.py`, `servicio/contratos.py`, `servicio/respaldo.py`, `escenarios.py`, `ejecutar_escenarios.py`, `registrar_ejecucion.py`, `verificar_ejecucion.py`, `verificar_registro.py`, `docs/bitacora_ajustes.md`, `docs/respaldos.md`, `docs/registro_ejecucion.md` |
| U3.5 | 2026-11-28 | Matrices QA (`MAT-1..MAT-6`), fundamentación mecánica, mitigaciones de seguridad y Matriz de Riesgos verificada (`RIE-1..RIE-6`) | `servicio/fundamentacion.py`, `servicio/seguridad.py`, `matriz_pruebas.py`, `verificar_matriz.py`, `verificar_mitigaciones.py`, `riesgos.py`, `verificar_riesgos.py`, `docs/matriz_pruebas.md`, `docs/registro_alucinaciones.md`, `docs/matriz_riesgos.md` |
| U3.6 | 2026-11-28 | README técnico completo, prueba en frío, API ejecutable, prueba de transferencia, decisiones y limitaciones | `verificar_readme.py`, `probar_en_frio.py`, `generar_api_md.py`, `verificar_transferencia.py`, `verificar_decisiones.py`, `docs/api.md`, `docs/decisiones.md`, `docs/limitaciones.md`, `docs/prueba_transferencia.md` |
