"""Ensayo del 429: varias llamadas cortas, sin pausa, contra Gemini.

Gasta cupo. Si el límite aparece, no volver a lanzarlo enseguida:
la cuota puede seguir llena. Si las diez salen bien, sube CALLS.
"""
import json
from datetime import datetime
from pathlib import Path

import client

CALLS = 10
QUESTION = "Di solo: ok"
OUTPUT = Path(__file__).resolve().parent.parent / "docs" / "rate-limit-drill.json"


def main() -> None:
    detail = []
    first_retry_on_call = None
    stopped_on_credentials = False

    for number in range(1, CALLS + 1):
        print(f"\n=== llamada {number} ===")
        waits: list[float] = []
        try:
            text = client.ask_model(QUESTION, system_instruction="", waits=waits)
            print(text)
            detail.append({
                "call": number,
                "ok": True,
                "waits_s": [round(wait, 3) for wait in waits],
                "text": text,
            })
        except ValueError as error:
            print("Credencial, no es el 429:", error)
            stopped_on_credentials = True
            detail.append({"call": number, "ok": False, "error": str(error)})
            break
        except RuntimeError as error:
            print(f"[{number}] intentos agotados:", error)
            detail.append({
                "call": number,
                "ok": False,
                "waits_s": [round(wait, 3) for wait in waits],
                "error": str(error),
            })

        if waits and first_retry_on_call is None:
            first_retry_on_call = number

    record = {
        "date": datetime.now().isoformat(timespec="seconds"),
        "calls_requested": CALLS,
        "question": QUESTION,
        "first_retry_on_call": first_retry_on_call,
        "stopped_on_credentials": stopped_on_credentials,
        "all_ok": all(item["ok"] for item in detail) and not stopped_on_credentials,
        "session_cost_usd": client.session_cost_usd,
        "calls": detail,
        "note": (
            "Una espera significa 429, un 5xx o un corte de red. "
            "El cliente ya tradujo el código antes de llegar aquí."
        ),
    }
    OUTPUT.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nCosto de la sesión: USD {client.session_cost_usd:.5f}")
    print(f"Registro en {OUTPUT}")


if __name__ == "__main__":
    main()
