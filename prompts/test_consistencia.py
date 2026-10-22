"""Corre cada prompt del banco 3 veces y guarda el conteo.

Éxito = JSON válido y con las claves de ese prompt.
"""
import json
import re
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from banco import BANCO_DE_PROMPTS
from consumir_gemini import build_request, extract_text, send_request

MODELO = "gemini-3.5-flash-lite"
REPETICIONES = 3
PAUSA_S = 1
SALIDA = Path(__file__).resolve().parent / "registro_resultados.json"


def parsear_respuesta(texto: str, claves: list[str]) -> dict:
    limpio = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        texto.strip(),
        flags=re.IGNORECASE | re.DOTALL,
    )
    datos = json.loads(limpio)
    if not isinstance(datos, dict):
        raise ValueError("La respuesta no es un objeto JSON")
    faltan = [clave for clave in claves if clave not in datos]
    if faltan:
        raise ValueError(f"Faltan claves: {', '.join(faltan)}")
    return datos


def una_corrida(prompt: dict) -> dict:
    url, headers, body = build_request(
        prompt["ejemplo_usuario"],
        MODELO,
        system_instruction=prompt["system_instruction"],
        response_schema=prompt.get("response_schema"),
    )
    data = send_request(url, headers, body)
    error = data.get("error")
    if error:
        codigo = error.get("code")
        raise RuntimeError(f"{codigo}: {error.get('message')}")
    texto = extract_text(data)
    return parsear_respuesta(texto, prompt["claves_esperadas"])


def main() -> None:
    registro = {"modelo": MODELO, "repeticiones": REPETICIONES, "prompts": {}}
    for indice, prompt in enumerate(BANCO_DE_PROMPTS):
        nombre = prompt["nombre"]
        print(f"\n=== {nombre} ===")
        corridas = []
        exitos = 0
        for i in range(1, REPETICIONES + 1):
            try:
                datos = una_corrida(prompt)
                exitos += 1
                corridas.append({"corrida": i, "ok": True, "datos": datos})
                print(f"[{i}] ok {datos}")
            except (ValueError, RuntimeError, json.JSONDecodeError) as error:
                corridas.append({"corrida": i, "ok": False, "error": str(error)})
                print(f"[{i}] fallo: {error}")
            queda_otra = indice < len(BANCO_DE_PROMPTS) - 1 or i < REPETICIONES
            if queda_otra:
                time.sleep(PAUSA_S)
        registro["prompts"][nombre] = {
            "exitos": exitos,
            "total": REPETICIONES,
            "corridas": corridas,
        }
        print(f"{nombre}: {exitos}/{REPETICIONES}")
    SALIDA.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nRegistro en {SALIDA}")


if __name__ == "__main__":
    main()
