"""Verificador de la entrega completa de U3.3 Bloque 38 (ENT-1 a ENT-7)."""
from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys

import yaml

RAIZ = Path(__file__).resolve().parent

SECCIONES = (
    "Requisitos",
    "Configuración",
    "Cómo arrancar",
    "Cómo comprobar que funciona",
    "Cómo detener",
    "Problemas frecuentes",
)
CRITERIOS = [f"VC-{n}" for n in range(1, 7)]
ESTADOS = ("PASA", "FALLA")
DECISIONES = ("aceptado", "rechazado", "aplazado")
RUTA_REVISION = Path("docs/verificacion_cruzada.md")


def leer(ruta: str | Path, raiz: Path = RAIZ) -> str | None:
    archivo = raiz / ruta
    return archivo.read_text(encoding="utf-8") if archivo.exists() else None


def configuracion(raiz: Path = RAIZ) -> dict | None:
    r = subprocess.run(
        ["docker", "compose", "config", "--format", "json"],
        cwd=str(raiz),
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode == 0 and r.stdout.strip():
        return json.loads(r.stdout)
    # Respaldo local cuando el plugin CLI no es accesible desde un entorno restringido.
    compose_file = raiz / "compose.yaml"
    if compose_file.exists():
        return yaml.safe_load(compose_file.read_text(encoding="utf-8"))
    return None


def composicion_valida(raiz: Path = RAIZ) -> tuple[bool, str]:
    datos = configuracion(raiz)
    if not isinstance(datos, dict) or "services" not in datos:
        return False, "docker compose config no pudo leer compose.yaml"
    servicios = datos["services"]
    if len(servicios) < 2:
        return False, f"hay {len(servicios)} servicio(s) y se piden 2"
    con_latest = [n for n, s in servicios.items() if str(s.get("image", "")).endswith(":latest")]
    if con_latest:
        return False, f"imagen con latest en: {con_latest}"
    dependencias = [n for n, s in servicios.items() if "depends_on" in s]
    if not dependencias:
        return False, "ningun servicio declara depends_on"
    return True, f"servicios {sorted(servicios)} con depends_on"


def readme_con_secciones(raiz: Path = RAIZ) -> tuple[bool, str]:
    texto = leer("README.md", raiz)
    if texto is None:
        return False, "no existe README.md"
    titulos = re.findall(r"^## (.+)$", texto, re.MULTILINE)
    faltan = [s for s in SECCIONES if s not in titulos]
    if faltan:
        return False, f"faltan secciones: {faltan}"
    return True, f"las {len(SECCIONES)} secciones estan"


def variables_documentadas(raiz: Path = RAIZ) -> tuple[bool, str]:
    ejemplo, readme = leer(".env.example", raiz), leer("README.md", raiz)
    if ejemplo is None or readme is None:
        return False, "falta .env.example o README.md"
    nombres = re.findall(r"^([A-Z][A-Z0-9_]*)=", ejemplo, re.MULTILINE)
    sin_doc = [n for n in nombres if n not in readme]
    if sin_doc:
        return False, f"variables sin explicar en el README: {sin_doc}"
    return True, f"el README explica {nombres}"


def archivos_existentes(raiz: Path = RAIZ) -> tuple[bool, str]:
    readme = leer("README.md", raiz)
    if readme is None:
        return False, "no existe README.md"
    patron = re.compile(r"`([A-Za-z0-9_./-]+\.(?:py|md|yaml|yml|txt|json|jsonl|png))`")
    citados = sorted(set(patron.findall(readme)))
    faltan = [a for a in citados if not (raiz / a).exists()]
    if faltan:
        return False, f"el README cita archivos que no existen: {faltan}"
    return True, f"existen los {len(citados)} archivos que cita"


def puertos_documentados(raiz: Path = RAIZ) -> tuple[bool, str]:
    datos = configuracion(raiz)
    readme = leer("README.md", raiz)
    if datos is None or readme is None:
        return False, "falta compose.yaml o README.md"
    puertos: set[str] = set()
    for servicio in datos.get("services", {}).values():
        for entrada in servicio.get("ports", []):
            if isinstance(entrada, dict) and "published" in entrada:
                puertos.add(str(entrada["published"]))
            elif isinstance(entrada, str) and ":" in entrada:
                puertos.add(entrada.split(":")[0].strip())
    sin_doc = sorted(p for p in puertos if p not in readme)
    if sin_doc:
        return False, f"puertos sin documentar: {sin_doc}"
    return True, f"el README documenta los puertos {sorted(puertos)}"


def revision_valida(raiz: Path = RAIZ) -> tuple[bool, str]:
    texto = leer(RUTA_REVISION, raiz)
    if texto is None:
        return False, f"no existe {RUTA_REVISION}"
    errores: list[str] = []
    for campo in ("Revisor", "Repositorio revisado", "Fecha"):
        if not re.search(rf"^{campo}: .+$", texto, re.MULTILINE):
            errores.append(f"falta '{campo}:'")
    if "Se siguió únicamente: README.md" not in texto:
        errores.append("falta 'Se siguió únicamente: README.md'")

    estados: dict[str, str] = {}
    for c in CRITERIOS:
        m = re.search(rf"^- {c} \([^)]+\): (\w+) - .+$", texto, re.MULTILINE)
        if not m or m.group(1) not in ESTADOS:
            errores.append(f"{c} sin resultado PASA o FALLA")
        else:
            estados[c] = m.group(1)

    hallazgos = re.findall(
        r"^- Hallazgo \d+ \((VC-\d)\): .+\n  Decisión: (\w+) - .+$",
        texto,
        re.MULTILINE,
    )
    for _, decision in hallazgos:
        if decision not in DECISIONES:
            errores.append(f"decision invalida: {decision}")

    citados = {c for c, _ in hallazgos}
    for c, estado in estados.items():
        if estado == "FALLA" and c not in citados:
            errores.append(f"{c} falla y no tiene hallazgo")

    if "Sin hallazgos" not in texto and not hallazgos:
        errores.append("sin hallazgos ni la frase 'Sin hallazgos'")

    if errores:
        return False, "; ".join(errores)
    return True, f"{len(estados)} criterios y {len(hallazgos)} hallazgos"


def sin_secretos(raiz: Path = RAIZ) -> tuple[bool, str]:
    r = subprocess.run(
        [sys.executable, str(raiz / "buscar_secretos.py")],
        cwd=str(raiz),
        capture_output=True,
        text=True,
        check=False,
    )
    ultima = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    return r.returncode == 0, ultima or "buscar_secretos.py fallo"


COMPROBACIONES = [
    ("ENT-1", "composicion con dos servicios", composicion_valida),
    ("ENT-2", "README con las secciones", readme_con_secciones),
    ("ENT-3", "variables explicadas", variables_documentadas),
    ("ENT-4", "archivos citados existen", archivos_existentes),
    ("ENT-5", "puertos documentados", puertos_documentados),
    ("ENT-6", "verificacion cruzada registrada", revision_valida),
    ("ENT-7", "sin secretos", sin_secretos),
]


def ejecutar(raiz: Path = RAIZ) -> bool:
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
