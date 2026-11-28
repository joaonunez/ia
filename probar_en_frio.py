"""Prueba en frío: clona el repositorio, prepara entorno aislado, corre pruebas y levanta la API (U3.6 · Bloque 44)."""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
WINDOWS = os.name == "nt"
PUERTO = 8000


def _puerto_libre(puerto: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", puerto)) != 0


def _detener(proceso: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
    if WINDOWS:
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proceso.pid)],
            capture_output=True,
            check=False,
        )
    else:
        proceso.terminate()
        proceso.wait(timeout=10)


def _pedir(ruta: str, metodo: str = "GET", cuerpo: dict | None = None) -> tuple[int, str]:
    datos = json.dumps(cuerpo).encode("utf-8") if cuerpo is not None else None
    req = urllib.request.Request(
        f"http://127.0.0.1:{PUERTO}{ruta}",
        data=datos,
        method=metodo,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, resp.read().decode("utf-8")


def ejecutar_prueba_en_frio() -> list[tuple[str, bool, str]]:
    resultados: list[tuple[str, bool, str]] = []
    tmp_dir = Path(tempfile.mkdtemp(prefix="jmx_ia_frio_"))
    clon = tmp_dir / "repo"
    proceso: subprocess.Popen[str] | None = None

    try:
        # FRIO-1: Clonar repositorio limpio
        r_clone = subprocess.run(
            ["git", "clone", "--no-hardlinks", str(REPO_ROOT), str(clon)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        ok1 = r_clone.returncode == 0 and (clon / "README.md").is_file() and (clon / "servicio" / "main.py").is_file()
        resultados.append(("FRIO-1", ok1, "repositorio clonado en carpeta limpia" if ok1 else r_clone.stderr.strip()))
        if not ok1:
            return resultados

        # FRIO-2: Validar importación del servicio desde el clon con el intérprete activo
        r_imp = subprocess.run(
            [sys.executable, "-c", "import servicio.main; print(servicio.main.app.title)"],
            cwd=str(clon),
            capture_output=True,
            text=True,
            timeout=30,
        )
        ok2 = r_imp.returncode == 0 and bool(r_imp.stdout.strip())
        resultados.append(("FRIO-2", ok2, f"servicio importable en clon ({r_imp.stdout.strip()})" if ok2 else r_imp.stderr.strip()))

        # FRIO-3: Ejecutar suite pytest sobre el clon
        r_test = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "tests/parciales"],
            cwd=str(clon),
            capture_output=True,
            text=True,
            timeout=90,
        )
        resumen_t = [ln.strip() for ln in r_test.stdout.splitlines() if ln.strip()][-1] if r_test.stdout.strip() else ""
        ok3 = r_test.returncode == 0
        resultados.append(("FRIO-3", ok3, resumen_t if ok3 else (r_test.stdout + r_test.stderr).strip()[:120]))

        # FRIO-4: Levantar uvicorn en puerto 8000 y verificar /health
        if not _puerto_libre(PUERTO):
            resultados.append(("FRIO-4", False, f"el puerto {PUERTO} está ocupado"))
            resultados.append(("FRIO-5", False, "omitido porque el servicio no arrancó"))
            return resultados

        entorno = dict(os.environ)
        entorno.pop("GEMINI_API_KEY", None)
        entorno["MODELO"] = "simulado"
        proceso = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "servicio.main:app", "--host", "127.0.0.1", "--port", str(PUERTO)],
            cwd=str(clon),
            env=entorno,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        salud_ok = False
        for _ in range(30):
            try:
                est, txt = _pedir("/health")
                if est == 200 and '"estado":"ok"' in txt:
                    salud_ok = True
                    break
            except Exception:
                time.sleep(0.3)
        resultados.append(("FRIO-4", salud_ok, "uvicorn levantó en :8000 y /health respondió 200" if salud_ok else "no respondió /health"))

        # FRIO-5: Consulta real con cita verificable
        if salud_ok:
            est_a, txt_a = _pedir(
                "/ask",
                metodo="POST",
                cuerpo={"pregunta": "¿Cuál es el porcentaje mínimo de asistencia para promoción escolar?"},
            )
            ok5 = est_a == 200 and "85 %" in txt_a and "reglamento_asistencia.md" in txt_a
            resultados.append(("FRIO-5", ok5, "POST /ask devolvió 85 % y reglamento_asistencia.md" if ok5 else f"respuesta inesperada: {txt_a[:80]}"))
        else:
            resultados.append(("FRIO-5", False, "no se pudo consultar /ask"))
    finally:
        if proceso is not None:
            _detener(proceso)
        shutil.rmtree(tmp_dir, ignore_errors=True)

    return resultados


def main() -> int:
    comprobaciones = ejecutar_prueba_en_frio()
    ok_count = 0
    for codigo, ok, detalle in comprobaciones:
        marca = "PASA " if ok else "FALLA"
        print(f"{marca} {codigo} -> {detalle}")
        if ok:
            ok_count += 1
    print(f"\n{ok_count} de {len(comprobaciones)} comprobaciones cumplidas")
    return 0 if ok_count == len(comprobaciones) else 1


if __name__ == "__main__":
    sys.exit(main())
