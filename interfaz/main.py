"""Interfaz web mínima para consultar la API del Asistente Académico IA (U3.3 · Bloque 38)."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse

API_URL = os.environ.get("API_URL", "http://api:8000")

app = FastAPI(title="Interfaz del Asistente Académico IA", version="0.1.0")

PAGINA = """<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Asistente Académico IA</title>
</head>
<body>
  <h1>Asistente Académico IA (Solo Lectura)</h1>
  <input id="q" size="55" placeholder="Ej: ¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?">
  <button onclick="preguntar()">Preguntar</button>
  <pre id="r"></pre>
  <script>
    async function preguntar() {
      const q = encodeURIComponent(document.getElementById("q").value);
      const r = await fetch("/preguntar?texto=" + q);
      document.getElementById("r").textContent = JSON.stringify(await r.json(), null, 2);
    }
  </script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def inicio() -> str:
    return PAGINA


@app.get("/health")
def health() -> dict[str, str]:
    return {"estado": "ok", "api": API_URL}


@app.get("/preguntar")
def preguntar(texto: str):
    datos = json.dumps({"pregunta": texto}).encode("utf-8")
    peticion = urllib.request.Request(
        f"{API_URL}/ask",
        data=datos,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=5) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        cuerpo = error.read().decode("utf-8")
        try:
            contenido = json.loads(cuerpo)
        except json.JSONDecodeError:
            contenido = {"codigo": "error_api", "mensaje": cuerpo}
        return JSONResponse(contenido, status_code=error.code)
    except OSError:
        return JSONResponse(
            {
                "codigo": "api_no_disponible",
                "mensaje": "No se pudo contactar a la API.",
            },
            status_code=502,
        )
