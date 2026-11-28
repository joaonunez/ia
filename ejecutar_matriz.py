"""Ejecutor genérico de matrices de pruebas con huella SHA-256 (U3.5 · Bloque 42).

Uso:
    python ejecutar_matriz.py --matriz matriz_pruebas --escribir
    python ejecutar_matriz.py --matriz matriz_modelo --escribir
    python ejecutar_matriz.py --matriz matriz_pruebas --url http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

import httpx
from fastapi.testclient import TestClient

from servicio.main import app

CLASIFICACIONES = ("defecto", "expectativa", "limitacion", "entorno")
REPO_ROOT = Path(__file__).resolve().parent


def cargar(nombre_modulo: str) -> list[dict[str, Any]]:
    """Importa un módulo de matriz por nombre y devuelve su lista `MATRIZ`."""
    modulo = importlib.import_module(nombre_modulo)
    matriz = getattr(modulo, "MATRIZ", None)
    if not isinstance(matriz, list):
        raise ValueError(f"El módulo '{nombre_modulo}' no exporta una lista MATRIZ.")
    return matriz


def registro_de(nombre_modulo: str) -> Path:
    """Devuelve la ruta de salida en `docs/` para una matriz dada."""
    return REPO_ROOT / "docs" / f"{nombre_modulo}.md"


def huella(matriz: list[dict[str, Any]]) -> str:
    """Calcula la huella SHA-256 (12 hex) determinista de la matriz."""
    serializado = json.dumps(matriz, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()[:12]


@contextmanager
def abrir_cliente(url: str | None = None) -> Iterator[Any]:
    """Abre un cliente HTTP contra `url` o un `TestClient(app)` en memoria."""
    if url:
        with httpx.Client(base_url=url.rstrip("/"), timeout=15.0) as cliente:
            yield cliente
    else:
        with TestClient(app) as cliente:
            yield cliente


def _texto_buscable(cuerpo: Any) -> str:
    if isinstance(cuerpo, dict) and "respuesta" in cuerpo and isinstance(cuerpo["respuesta"], str):
        return cuerpo["respuesta"] + " " + json.dumps(cuerpo, ensure_ascii=False)
    if isinstance(cuerpo, (dict, list)):
        return json.dumps(cuerpo, ensure_ascii=False)
    return str(cuerpo)


def motivos_de_falla(caso: dict[str, Any], estado: int, cuerpo: Any) -> list[str]:
    """Evalúa las aserciones declaradas en `caso['esperado']`."""
    esperado = caso["esperado"]
    motivos: list[str] = []

    if estado != esperado["estado"]:
        motivos.append(f"estado={estado} (esperado {esperado['estado']})")

    texto = _texto_buscable(cuerpo).lower()
    for sub in esperado.get("contiene", []):
        if str(sub).lower() not in texto:
            motivos.append(f"falta texto esperado: {sub!r}")

    for sub in esperado.get("no_contiene", []):
        if str(sub).lower() in texto:
            motivos.append(f"contiene texto prohibido: {sub!r}")

    if "fuentes" in esperado:
        fuentes_esp = esperado["fuentes"]
        fuentes_real = cuerpo.get("fuentes") if isinstance(cuerpo, dict) else None
        if fuentes_esp == []:
            if fuentes_real != []:
                motivos.append(f"fuentes={fuentes_real!r} (esperado [])")
        else:
            if not isinstance(fuentes_real, list):
                motivos.append(f"fuentes no es lista: {fuentes_real!r}")
            else:
                for fuente in fuentes_esp:
                    if fuente not in fuentes_real:
                        motivos.append(f"falta fuente: {fuente!r}")

    return motivos


def ejecutar(matriz: list[dict[str, Any]], url: str | None = None) -> list[dict[str, Any]]:
    """Ejecuta todos los escenarios de `matriz` y devuelve sus resultados."""
    resultados: list[dict[str, Any]] = []
    with abrir_cliente(url) as cliente:
        for caso in matriz:
            pet = caso["peticion"]
            metodo = pet["metodo"].upper()
            ruta = pet["ruta"]
            kwargs: dict[str, Any] = {}
            if "json" in pet:
                kwargs["json"] = pet["json"]
            if "headers" in pet:
                kwargs["headers"] = pet["headers"]

            try:
                resp = cliente.request(metodo, ruta, **kwargs)
                estado = resp.status_code
                try:
                    cuerpo = resp.json()
                except Exception:
                    cuerpo = resp.text
                motivos = motivos_de_falla(caso, estado, cuerpo)
            except Exception as exc:
                estado = 0
                cuerpo = str(exc)
                motivos = [f"error de conexión: {exc}"]

            resultados.append(
                {
                    "id": caso["id"],
                    "tipo": caso["tipo"],
                    "escenario": caso["escenario"],
                    "cubre": caso["cubre"],
                    "estado": estado,
                    "resultado": "PASA" if not motivos else "FALLA",
                    "motivos": motivos,
                    "hallazgo": caso.get("hallazgo"),
                }
            )
    return resultados


def resumen(resultados: list[dict[str, Any]]) -> dict[str, int]:
    """Agrega totales de ejecución de la matriz."""
    pasan = sum(1 for r in resultados if r["resultado"] == "PASA")
    fallan = sum(1 for r in resultados if r["resultado"] == "FALLA")
    limitaciones = sum(
        1
        for r in resultados
        if r["resultado"] == "FALLA"
        and isinstance(r.get("hallazgo"), dict)
        and r["hallazgo"].get("clasificacion") == "limitacion"
    )
    sin_clasificar = sum(
        1 for r in resultados if r["resultado"] == "FALLA" and not r.get("hallazgo")
    )
    return {
        "total": len(resultados),
        "pasan": pasan,
        "fallan": fallan,
        "limitaciones": limitaciones,
        "sin_clasificar": sin_clasificar,
    }


def imprimir(nombre_modulo: str, matriz: list[dict[str, Any]], resultados: list[dict[str, Any]]) -> None:
    """Imprime un resumen legible por consola."""
    res = resumen(resultados)
    print(f"Matriz: {nombre_modulo} (huella {huella(matriz)})")
    for r in resultados:
        detalle = ""
        if r["resultado"] == "FALLA":
            clasif = (r.get("hallazgo") or {}).get("clasificacion", "sin clasificar")
            detalle = f" [{clasif}] -> {'; '.join(r['motivos'])}"
        print(f"  {r['id']} ({r['tipo']:8s}) {r['resultado']:5s} HTTP {r['estado']}{detalle}")
    print(
        f"Resumen: {res['pasan']}/{res['total']} PASA, "
        f"{res['fallan']} FALLA ({res['limitaciones']} limitaciones declaradas)."
    )


def escribir_registro(
    nombre_modulo: str,
    matriz: list[dict[str, Any]],
    resultados: list[dict[str, Any]],
) -> Path:
    """Escribe el registro Markdown verificable en `docs/<nombre_modulo>.md`."""
    destino = registro_de(nombre_modulo)
    destino.parent.mkdir(parents=True, exist_ok=True)
    res = resumen(resultados)
    fecha = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    h = huella(matriz)

    lineas = [
        f"# Registro de Matriz de Pruebas — `{nombre_modulo}`",
        "",
        f"- **Fecha de ejecución:** {fecha}",
        f"- **Huella de la matriz:** {h}",
        f"- **Escenarios ejecutados:** {res['total']}",
        f"- **Resultado:** {res['pasan']} PASA · {res['fallan']} FALLA · {res['limitaciones']} limitaciones declaradas",
        "",
        "## Resultados por escenario",
        "",
        "| ID | Tipo | Cubre | HTTP | Resultado | Escenario |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in resultados:
        cubre = ", ".join(r["cubre"])
        lineas.append(
            f"| {r['id']} | {r['tipo']} | {cubre} | {r['estado']} | {r['resultado']} | {r['escenario']} |"
        )

    hallazgos = [r for r in resultados if r["resultado"] == "FALLA"]
    if hallazgos:
        lineas.extend(["", "## Hallazgos y limitaciones declaradas", ""])
        for r in hallazgos:
            h_info = r.get("hallazgo") or {}
            clasif = h_info.get("clasificacion", "sin clasificar")
            decision = h_info.get("decision", "Sin decisión registrada.")
            motivos = "; ".join(r["motivos"])
            lineas.extend(
                [
                    f"### {r['id']} — {clasif}",
                    f"- **Escenario:** {r['escenario']}",
                    f"- **Motivo observado:** {motivos}",
                    f"- **Decisión:** {decision}",
                    "",
                ]
            )

    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return destino


def main() -> int:
    parser = argparse.ArgumentParser(description="Ejecuta una matriz de pruebas QA.")
    parser.add_argument("--matriz", default="matriz_pruebas", help="Módulo Python que exporta MATRIZ.")
    parser.add_argument("--url", default=None, help="URL base opcional del servicio en vivo.")
    parser.add_argument("--escribir", action="store_true", help="Escribe docs/<matriz>.md.")
    args = parser.parse_args()

    matriz = cargar(args.matriz)
    resultados = ejecutar(matriz, url=args.url)
    imprimir(args.matriz, matriz, resultados)
    if args.escribir:
        ruta = escribir_registro(args.matriz, matriz, resultados)
        print(f"Registro escrito en {ruta}")

    # Falla solo si hay FALLA sin clasificar o clasificada fuera de limitacion
    no_aceptadas = [
        r
        for r in resultados
        if r["resultado"] == "FALLA"
        and (not isinstance(r.get("hallazgo"), dict) or r["hallazgo"].get("clasificacion") != "limitacion")
    ]
    return 1 if no_aceptadas else 0


if __name__ == "__main__":
    sys.exit(main())
