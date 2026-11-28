"""Verifica el plan de pruebas parciales y el aislamiento de cada suite (U3.4 · Bloque 39)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

PLAN = Path("docs/pruebas_parciales.md")
COLUMNAS = [
    "Componente",
    "Entrada",
    "Salida",
    "Doble",
    "Archivo",
    "Defecto introducido",
    "Detectado",
]
MINIMO_COMPONENTES = 4
MINIMO_PRUEBAS = 3

PROHIBIDO = {
    r"^\s*(?:import|from)\s+(?:httpx|requests|socket|urllib|subprocess)\b": "usa red o procesos",
    r"^\s*(?:import|from)\s+docker\b": "usa Docker",
    r"\bTestClient\b": "usa el cliente HTTP de FastAPI",
    r"\bservicio\.main\b|from servicio import .*\bmain\b": "importa la aplicacion",
    r"\bos\.environ\b|\bos\.getenv\b|dotenv": "lee el entorno real (usa monkeypatch)",
}


def filas_del_plan(raiz: Path = Path(".")) -> list[dict[str, str]] | None:
    plan = raiz / PLAN
    if not plan.exists():
        return None
    filas: list[dict[str, str]] = []
    for linea in plan.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("|"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if celdas[0] == "Componente" or set(celdas[0]) <= set("-: "):
            continue
        if len(celdas) == len(COLUMNAS):
            filas.append(dict(zip(COLUMNAS, celdas)))
    return filas


def archivos_del_plan(raiz: Path = Path(".")) -> list[Path]:
    return [raiz / f["Archivo"] for f in (filas_del_plan(raiz) or [])]


def plan_completo(raiz: Path = Path(".")) -> tuple[bool, str]:
    filas = filas_del_plan(raiz)
    if filas is None:
        return False, f"no existe {PLAN}"
    if len(filas) < MINIMO_COMPONENTES:
        return False, f"hay {len(filas)} componente(s) y se piden {MINIMO_COMPONENTES}"
    problemas: list[str] = []
    for f in filas:
        vacias = [c for c in COLUMNAS[:5] if not f[c]]
        if vacias:
            problemas.append(f"{f['Componente']}: vacio {vacias}")
        elif not (raiz / f["Archivo"]).exists():
            problemas.append(f"{f['Componente']}: no existe {f['Archivo']}")
    if problemas:
        return False, "; ".join(problemas)
    return True, f"{len(filas)} componentes con sus archivos"


def pruebas_suficientes(raiz: Path = Path(".")) -> tuple[bool, str]:
    archivos = archivos_del_plan(raiz)
    if not archivos:
        return False, "el plan no tiene archivos"
    problemas: list[str] = []
    for a in archivos:
        if not a.exists():
            continue
        texto = a.read_text(encoding="utf-8")
        pruebas = re.findall(r"^def (test_\w+)", texto, re.MULTILINE)
        if len(pruebas) < MINIMO_PRUEBAS:
            problemas.append(f"{a.name}: {len(pruebas)} prueba(s)")
        elif not any(p.startswith("test_contrato") for p in pruebas):
            problemas.append(f"{a.name}: sin test_contrato")
    if problemas:
        return False, "; ".join(problemas)
    return True, f"{len(archivos)} archivos con 3+ pruebas y contrato"


def pruebas_aisladas(raiz: Path = Path(".")) -> tuple[bool, str]:
    archivos = archivos_del_plan(raiz)
    if not archivos:
        return False, "el plan no tiene archivos"
    problemas: list[str] = []
    for a in archivos:
        if not a.exists():
            continue
        for n, linea in enumerate(a.read_text(encoding="utf-8").splitlines(), 1):
            for patron, motivo in PROHIBIDO.items():
                if re.search(patron, linea):
                    problemas.append(f"{a.name}:{n} {motivo}")
    if problemas:
        return False, "; ".join(problemas)
    return True, "sin red, sin Docker, sin entorno real"


def pruebas_pasan(raiz: Path = Path(".")) -> tuple[bool, str]:
    archivos = archivos_del_plan(raiz)
    if not archivos:
        return False, "el plan no tiene archivos"
    problemas: list[str] = []
    total = 0
    for a in archivos:
        if not a.exists():
            continue
        r = subprocess.run(
            [sys.executable, "-m", "pytest", str(a), "-q", "--tb=no"],
            cwd=str(raiz),
            capture_output=True,
            text=True,
            check=False,
        )
        resumen = (r.stdout.strip().splitlines() or [""])[-1]
        pasan = re.search(r"(\d+) passed", resumen)
        total += int(pasan.group(1)) if pasan else 0
        if r.returncode != 0:
            problemas.append(f"{a.name}: {resumen}")
    if problemas:
        return False, "; ".join(problemas)
    return True, f"pasan {total} pruebas"


def defectos_detectados(raiz: Path = Path(".")) -> tuple[bool, str]:
    filas = filas_del_plan(raiz) or []
    problemas: list[str] = []
    for f in filas:
        if not f["Defecto introducido"]:
            problemas.append(f"{f['Componente']}: sin defecto anotado")
        elif f["Detectado"].lower() not in ("si", "sí"):
            problemas.append(f"{f['Componente']}: Detectado = {f['Detectado']!r}")
    if not filas:
        return False, "el plan no tiene filas"
    if problemas:
        return False, "; ".join(problemas)
    return True, f"{len(filas)} defectos detectados"


COMPROBACIONES = [
    ("PAR-1", "plan con sus componentes y archivos", plan_completo),
    ("PAR-2", "3+ pruebas y una de contrato", pruebas_suficientes),
    ("PAR-3", "pruebas aisladas", pruebas_aisladas),
    ("PAR-4", "las pruebas pasan", pruebas_pasan),
    ("PAR-5", "cada defecto fue detectado", defectos_detectados),
]


def ejecutar(raiz: Path = Path(".")) -> bool:
    cumplidas = 0
    for id_, descripcion, prueba in COMPROBACIONES:
        try:
            ok, evidencia = prueba(raiz)
        except Exception as error:
            ok, evidencia = False, f"error: {error!r}"
        estado = "PASA " if ok else "FALLA"
        print(f"{estado} {id_} {descripcion} -> {evidencia}")
        cumplidas += 1 if ok else 0
    total = len(COMPROBACIONES)
    print(f"\n{cumplidas} de {total} comprobaciones cumplidas")
    return cumplidas == total


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar() else 1)
