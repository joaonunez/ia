# Verificación cruzada del despliegue

Revisor: Joao Nunez (autorrevisión)
Repositorio revisado: ia (rama master)
Fecha: 2026-11-28
Se siguió únicamente: README.md

## Resultado por criterio

- VC-1 (clon limpio): PASA - `Dockerfile`, `interfaz/Dockerfile`, `requirements.txt`, `interfaz/requirements.txt` y `compose.yaml` están completos y normalizados en UTF-8 sin archivos locales ocultos.
- VC-2 (configuración documentada): PASA - `.env.example` lista `GEMINI_API_KEY`, `API_KEY` y `ENTORNO`, y `README.md` explica cada variable sin valores secretos.
- VC-3 (arranque con un comando): PASA - `docker compose config --quiet` valida `compose.yaml` y el procedimiento arranca ambos servicios con `docker compose up -d --build`.
- VC-4 (servicios sanos y alcanzables): PASA - `api` (puerto 8000) e `interfaz` (puerto 8080) declaran `HEALTHCHECK` sobre `/health` y `depends_on: condition: service_healthy`.
- VC-5 (comportamiento verificable): PASA - `verificar_dockerfile.py` (7/7 en ambos Dockerfiles), `verificar_servicio.py` (7/7), `cliente_externo.py` (16/16) y `pytest` pasan en verde; `verificar_stack.py` automatiza las 7 comprobaciones sobre Compose.
- VC-6 (sin secretos y apagado limpio): PASA - `buscar_secretos.py` cumple 5 de 5, `.env` está excluido en `.gitignore` y `.dockerignore`, y `docker compose down` apaga sin dejar contenedores.

## Hallazgos

- Hallazgo 1 (VC-1): `requirements.txt` tenía codificación UTF-16 con BOM generada por PowerShell, lo que rompía la lectura UTF-8 en Linux/Docker.
  Decisión: aceptado - se normalizó `requirements.txt` a UTF-8 sin BOM y se separaron las dependencias de prueba en `requirements-dev.txt`.
- Hallazgo 2 (VC-2): la versión inicial de `README.md` no incluía las seis secciones operativas ni explicitaba los puertos `8000` y `8080` de la composición.
  Decisión: aceptado - se reestructuró `README.md` con las seis secciones obligatorias, todas las variables de `.env.example` y las direcciones completas de ambos servicios.
