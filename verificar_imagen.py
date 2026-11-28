"""Verifica una imagen Docker en ejecución contra los criterios de U3.3 Bloque 37.

Uso:
    docker build -t asistente-academico:0.1 .
    python verificar_imagen.py asistente-academico:0.1
"""
from __future__ import annotations

import subprocess
import sys
import time

import httpx2

from casos import CASOS, ejecutar_caso

CONTENEDOR = "verificacion-asistente-ia"
PUERTO = 8099


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def verificar_imagen(imagen: str = "asistente-academico:0.1") -> bool:
    # Comprobar motor Docker activo
    ping = _run(["docker", "info", "--format", "{{.ServerVersion}}"])
    if ping.returncode != 0:
        print("ERROR: Docker no responde. Abre Docker Desktop y verifica con `docker ps`.")
        return False

    _run(["docker", "rm", "-f", CONTENEDOR])
    arranque = _run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            CONTENEDOR,
            "-p",
            f"{PUERTO}:8000",
            imagen,
        ]
    )
    if arranque.returncode != 0:
        print(f"ERROR al iniciar el contenedor: {arranque.stderr.strip()}")
        return False

    try:
        # 1. Esperar estado healthy
        salud = "starting"
        for _ in range(30):
            ins = _run(["docker", "inspect", "--format", "{{.State.Health.Status}}", CONTENEDOR])
            salud = ins.stdout.strip()
            if salud == "healthy":
                break
            time.sleep(1.0)
        ok_health = salud == "healthy"
        print(f"{'PASA ' if ok_health else 'FALLA'} IMG-01 estado de salud -> {salud}")

        # 2. Verificar usuario no-root
        who = _run(["docker", "exec", CONTENEDOR, "id", "-u"])
        uid = who.stdout.strip()
        ok_user = uid.isdigit() and uid != "0"
        print(f"{'PASA ' if ok_user else 'FALLA'} IMG-02 usuario sin privilegios -> uid={uid}")

        # 3. Verificar ausencia de secretos y archivos excluidos en /app
        ls = _run(["docker", "exec", CONTENEDOR, "ls", "-a", "/app"])
        entradas = set(ls.stdout.split())
        prohibidos = sorted(entradas & {".env", ".git", ".venv", "tests", "docs"})
        ok_clean = not prohibidos
        print(
            f"{'PASA ' if ok_clean else 'FALLA'} IMG-03 imagen sin secretos ni archivos excluidos -> "
            f"{'limpia' if ok_clean else f'encontrados: {prohibidos}'}"
        )

        # 4. Ejecutar batería de casos externa contra el contenedor
        base_url = f"http://127.0.0.1:{PUERTO}"
        aprobados = 0
        with httpx2.Client(base_url=base_url, timeout=10.0) as cliente:
            for caso in CASOS:
                ok, estado, detalle = ejecutar_caso(cliente, caso)
                marca = "PASA " if ok else "FALLA"
                print(f"{marca} {caso['id']:4s} [{estado}] {caso['descripcion']} -> {detalle}")
                if ok:
                    aprobados += 1

        ok_casos = aprobados == len(CASOS)
        print(f"\nCasos HTTP contra contenedor: {aprobados}/{len(CASOS)} aprobados")
        return ok_health and ok_user and ok_clean and ok_casos
    finally:
        _run(["docker", "rm", "-f", CONTENEDOR])


if __name__ == "__main__":
    nombre_imagen = sys.argv[1] if len(sys.argv) > 1 else "asistente-academico:0.1"
    raise SystemExit(0 if verificar_imagen(nombre_imagen) else 1)
