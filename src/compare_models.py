"""Compara 3 modelos Gemini con el mismo prompt del asistente de gestor académico.

Mide latencia (time.perf_counter), costo (calculate_cost) y acierto de la respuesta.
Precios: https://ai.google.dev/gemini-api/docs/pricing (Standard, paid tier,
texto, consultados el 2026-10-21; página "Last updated 2026-10-19 UTC").
"""
import json
import time
from pathlib import Path

from gemini_api import build_request, calculate_cost, extract_text, send_request

# Precios en USD por token (precio por 1M tokens / 1_000_000)
MODELS: dict[str, dict[str, float]] = {
    "gemini-3.5-flash-lite": {"input": 0.30 / 1_000_000, "output": 2.50 / 1_000_000},
    "gemini-3-flash-preview": {"input": 0.50 / 1_000_000, "output": 3.00 / 1_000_000},
    "gemini-3.8-flash": {"input": 0.75 / 1_000_000, "output": 3.75 / 1_000_000},
}
RUNS = 4
EXPECTED = "Diego Soto"

PROMPT = """Eres el asistente de solo lectura del gestor académico de una intranet escolar.
Responde solo con los datos entregados, en una o dos frases.

Datos ficticios del curso 2°B (Matemáticas, escala 1.0 a 7.0, nota mínima de aprobación 4.0):
- Ana Rojas: notas 6.1, 5.8, 6.4; asistencia 95%
- Diego Soto: notas 3.5, 4.1, 3.6; asistencia 72%
- Camila Pérez: notas 5.0, 4.7, 5.3; asistencia 88%
- Matías Fuentes: notas 4.2, 3.9, 4.5; asistencia 91%

Pregunta: ¿Qué estudiante tiene promedio bajo 4.0 y además asistencia menor a 85%?
Indica su nombre, su promedio con un decimal y su asistencia."""

OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "resultados-comparacion.json"


def send_with_backoff(url: str, headers: dict, body: dict, retries: int = 5) -> tuple[dict, float, int]:
    """Envía la petición con backoff exponencial simple ante 429/503 o timeout.

    Devuelve (data, latencia del intento exitoso en segundos, reintentos usados).
    """
    wait = 2.0
    for attempt in range(retries):
        last = attempt == retries - 1
        start = time.perf_counter()
        try:
            data = send_request(url, headers, body)
        except RuntimeError as error:
            if last:
                raise
            print(f"  {error} Esperando {wait:.0f} s...")
            time.sleep(wait)
            wait *= 2
            continue
        latency = time.perf_counter() - start
        error = data.get("error")
        if error and error.get("code") in (429, 503) and not last:
            print(f"  {error.get('code')} recibido, esperando {wait:.0f} s...")
            time.sleep(wait)
            wait *= 2
            continue
        if error:
            raise RuntimeError(f"Error de la API {error.get('code')}: {error.get('message')}")
        return data, latency, attempt
    raise RuntimeError("Se agotaron los reintentos.")


def is_correct(text: str) -> bool:
    return EXPECTED.lower() in text.lower() and "3.7" in text.replace(",", ".")


def run() -> dict:
    results: dict = {"prompt": PROMPT, "expected": "Diego Soto, promedio 3.7, asistencia 72%", "models": {}}
    for model, prices in MODELS.items():
        print(f"\n=== {model} ===")
        runs = []
        for i in range(1, RUNS + 1):
            # La medición del 21-10 llevó el rol dentro del prompt. Se repite igual.
            url, headers, body = build_request(PROMPT, model, system_instruction="")
            data, latency, retries = send_with_backoff(url, headers, body)
            text = extract_text(data).strip()
            cost = calculate_cost(data, prices["input"], prices["output"])
            usage = data.get("usageMetadata", {})
            ok = is_correct(text)
            runs.append({
                "run": i, "latency_s": round(latency, 3), "cost_usd": cost,
                "prompt_tokens": usage.get("promptTokenCount"),
                "output_tokens": usage.get("candidatesTokenCount"),
                "thoughts_tokens": usage.get("thoughtsTokenCount", 0),
                "retries": retries, "correct": ok, "text": text,
            })
            print(f"[{i}] latencia {latency:.2f} s | costo USD {cost:.6f} | correcta: {ok}")
            print(f"    {text}")
        avg_lat = sum(r["latency_s"] for r in runs) / RUNS
        total = sum(r["cost_usd"] for r in runs)
        hits = sum(r["correct"] for r in runs)
        results["models"][model] = {
            "price_input_per_1m": prices["input"] * 1_000_000,
            "price_output_per_1m": prices["output"] * 1_000_000,
            "avg_latency_s": round(avg_lat, 3), "avg_cost_usd": total / RUNS,
            "total_cost_usd": total, "correct": f"{hits}/{RUNS}", "runs": runs,
        }
        print(f"Promedio {model}: latencia {avg_lat:.2f} s | costo prom. USD {total / RUNS:.6f} | total USD {total:.6f} | aciertos {hits}/{RUNS}")
    OUTPUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados guardados en {OUTPUT}")
    return results


if __name__ == "__main__":
    try:
        run()
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la comparación:", error)
