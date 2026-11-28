# Diario de fricción de documentación

Registro de tropiezos observados al ejecutar el proyecto desde cero siguiendo únicamente el `README.md`.

| Nº | Qué pasó | Qué faltaba | Sección |
| --- | --- | --- | --- |
| 1 | Al activar el entorno en PowerShell apareció error de política de ejecución de scripts | Indicar `Set-ExecutionPolicy -Scope Process RemoteSigned` junto a la activación en Windows | Instalación |
| 2 | `/health` mostró `"modelo": "sin clave"` y generó duda sobre si era un fallo | Aclarar que sin `GEMINI_API_KEY` arranca en modo simulado local y qué cambia al configurarla | Configuración |
| 3 | Al levantar sin Docker con `MODELO=real` sin clave devolvió HTTP 503 | Documentar explícitamente el comando `uvicorn`, `MODELO` y `PERMITIR_RESPALDO` | Cómo arrancar |
| 4 | Una consulta con sinónimos puros devolvió `SIN_INFORMACION` | Enlazar las limitaciones conocidas (`docs/limitaciones.md`) directamente desde el README | Limitaciones |
