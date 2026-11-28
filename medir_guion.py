"""Medidor y verificador del guion de defensa técnica `docs/defensa.md` (U3.7 · Bloque S2).

Comprueba 9 reglas (`GUION-1..GUION-9`):
- GUION-1: 5 secciones con tiempos que suman exactamente 8 minutos.
- GUION-2: palabras habladas dentro del presupuesto por sección (130 pal/min).
- GUION-3: todos los identificadores citados (R-, D-, LIM-, T-, A-, H-) existen.
- GUION-4: nombra los riesgos de mayor puntaje residual.
- GUION-5: cifras citadas (pruebas, riesgos, ejemplos) coinciden con el proyecto.
- GUION-6: tecnologías citadas existen en el código/configuración del repo.
- GUION-7: tabla de diapositivas (<= 8) cubre las 5 secciones.
- GUION-8: pasos `PASO-n` en Demo coinciden con `ensayo_demo.PASOS`.
- GUION-9: sin marcadores pendientes (`[COMPLETAR]`, `TODO`) ni secretos.
"""
from __future__ import annotations

import re
import subprocess
import sys
import unicodedata
from pathlib import Path

import alucinaciones
import ataques
import ejemplos_api
import riesgos
import transferencia
import verificar_decisiones
from buscar_secretos import ASIGNACION, CLAVE_GOOGLE

REPO_ROOT = Path(__file__).resolve().parent
GUION = REPO_ROOT / "docs" / "defensa.md"
PALABRAS_POR_MINUTO = 130
MINUTOS_TOTALES = 8

SECCIONES_ESPERADAS = [
    ("problema", 1, True),
    ("arquitectura", 2, True),
    ("riesgos", 2, True),
    ("demo", 2, False),
    ("cierre", 1, True),
]

TECNOLOGIAS_CANDIDATAS = (
    "FastAPI",
    "Docker",
    "Pydantic",
    "uvicorn",
    "Chroma",
    "Gemini",
    "LangChain",
    "Kubernetes",
    "Terraform",
    "Redis",
    "PostgreSQL",
)


def normal(texto: str) -> str:
    n = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in n if not unicodedata.combining(c)).casefold().strip()


def palabras(texto: str) -> int:
    return len(re.findall(r"\b[\wÁÉÍÓÚáéíóúÑñ-]+\b", texto))


def cuerpo_de(texto: str, clave: str) -> str:
    encabezados = list(re.finditer(r"^##\s+(.+)$", texto, re.M))
    for i, m in enumerate(encabezados):
        if normal(clave) in normal(m.group(1)):
            inicio = m.end()
            fin = encabezados[i + 1].start() if i + 1 < len(encabezados) else len(texto)
            return texto[inicio:fin].strip()
    return ""


def comprobar_guion1(texto: str) -> tuple[bool, str]:
    encontrados = re.findall(r"^##\s+\d+\.\s+([^\n(]+)\((\d+)\s*min\)", texto, re.M)
    if len(encontrados) != 5:
        return False, f"se esperan 5 secciones con tiempo, hay {len(encontrados)}"
    suma = sum(int(mins) for _, mins in encontrados)
    if suma != MINUTOS_TOTALES:
        return False, f"los tiempos suman {suma} min y deben sumar {MINUTOS_TOTALES}"
    for (nombre, mins), (clave, esp_min, _) in zip(encontrados, SECCIONES_ESPERADAS):
        if clave not in normal(nombre) or int(mins) != esp_min:
            return False, f"sección '{nombre.strip()} ({mins} min)' no calza con '{clave} ({esp_min} min)'"
    return True, f"5 secciones, {suma} minutos en total"


def comprobar_guion2(texto: str) -> tuple[bool, str]:
    detalles: list[str] = []
    excedidas: list[str] = []
    for clave, mins, se_lee in SECCIONES_ESPERADAS:
        if not se_lee:
            continue
        tope = mins * PALABRAS_POR_MINUTO
        n = palabras(cuerpo_de(texto, clave))
        detalles.append(f"{clave} {n}/{tope}")
        if n == 0 or n > tope:
            excedidas.append(f"{clave} ({n}/{tope})")
    if excedidas:
        return False, f"fuera de presupuesto: {', '.join(excedidas)}"
    return True, "; ".join(detalles)


def _identificadores_validos() -> set[str]:
    validos = {r["id"] for r in riesgos.RIESGOS}
    validos |= {a["id"] for a in ataques.ATAQUES}
    validos |= {b["id"] for b in ataques.LEGITIMAS}
    validos |= {s["id"] for s in alucinaciones.SONDAS}
    validos |= {t["id"] for t in transferencia.PRUEBA["tareas"]}
    dec = verificar_decisiones.parsear_decisiones(
        verificar_decisiones.DECISIONES_MD.read_text(encoding="utf-8")
    )
    lim = verificar_decisiones.parsear_limitaciones(
        verificar_decisiones.LIMITACIONES_MD.read_text(encoding="utf-8")
    )
    validos |= {d["id"] for d in dec}
    validos |= {x["id"] for x in lim}
    return validos


def comprobar_guion3(texto: str) -> tuple[bool, str]:
    citados = sorted(set(re.findall(r"\b(?:R|D|LIM|T|A|H)-\d+\b", texto)))
    validos = _identificadores_validos()
    inexistentes = [c for c in citados if c not in validos]
    if inexistentes:
        return False, f"identificadores inexistentes: {inexistentes}"
    return True, f"{len(citados)} identificadores citados, todos existen"


def comprobar_guion4(texto: str) -> tuple[bool, str]:
    max_res = max(int(r["residual"]) for r in riesgos.RIESGOS)
    mayores = sorted(r["id"] for r in riesgos.RIESGOS if int(r["residual"]) == max_res)
    faltan = [rid for rid in mayores if rid not in texto]
    if faltan:
        return False, f"no nombra riesgos de mayor residual ({max_res}): {faltan}"
    return True, f"se nombran los de residual {max_res}: {', '.join(mayores)}"


def _contar_pruebas_reales() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=120,
    )
    m = re.search(r"(\d+)\s+passed", proc.stdout + proc.stderr)
    return int(m.group(1)) if m else 0


def comprobar_guion5(texto: str, total_pruebas: int | None = None) -> tuple[bool, str]:
    errores: list[str] = []
    citadas = 0

    m_pruebas = re.search(r"\b(\d+)\s+pruebas\b", texto)
    if m_pruebas:
        citadas += 1
        dicho = int(m_pruebas.group(1))
        real = total_pruebas if total_pruebas is not None else _contar_pruebas_reales()
        if dicho != real:
            errores.append(f"dice {dicho} pruebas y hay {real}")

    m_riesgos = re.search(r"\b(\d+)\s+riesgos\b", texto)
    if m_riesgos:
        citadas += 1
        dicho = int(m_riesgos.group(1))
        if dicho != len(riesgos.RIESGOS):
            errores.append(f"dice {dicho} riesgos y hay {len(riesgos.RIESGOS)}")

    m_ejemplos = re.search(r"\b(\d+)\s+ejemplos\b", texto)
    if m_ejemplos:
        citadas += 1
        dicho = int(m_ejemplos.group(1))
        if dicho != len(ejemplos_api.EJEMPLOS):
            errores.append(f"dice {dicho} ejemplos y hay {len(ejemplos_api.EJEMPLOS)}")

    if citadas == 0:
        return False, "el guion no cita cifras verificables (pruebas/riesgos/ejemplos)"
    if errores:
        return False, "; ".join(errores)
    return True, f"{citadas} cifras citadas, todas coinciden"


def comprobar_guion6(texto: str) -> tuple[bool, str]:
    archivos_ref = (
        REPO_ROOT / "requirements.txt",
        REPO_ROOT / "requirements-dev.txt",
        REPO_ROOT / "compose.yaml",
        REPO_ROOT / "Dockerfile",
        REPO_ROOT / "servicio" / "main.py",
        REPO_ROOT / "servicio" / "logica.py",
    )
    corpus_repo = "\n".join(
        [p.name + "\n" + p.read_text(encoding="utf-8", errors="ignore") for p in archivos_ref if p.exists()]
    ).lower()

    mencionadas = [t for t in TECNOLOGIAS_CANDIDATAS if re.search(rf"\b{re.escape(t)}\b", texto, re.I)]
    inexistentes = [t for t in mencionadas if t.lower() not in corpus_repo]
    if inexistentes:
        return False, f"tecnologías citadas ausentes del proyecto: {inexistentes}"
    return True, f"todas existen en el proyecto: {', '.join(mencionadas)}"


def comprobar_guion7(texto: str) -> tuple[bool, str]:
    cuerpo = cuerpo_de(texto, "diapositivas")
    filas = []
    for linea in cuerpo.splitlines():
        s = linea.strip()
        if s.startswith("|") and s.endswith("|"):
            celdas = [c.strip() for c in s.strip("|").split("|")]
            if len(celdas) == 3 and celdas[0].isdigit():
                filas.append(celdas)
    if not filas or len(filas) > 8:
        return False, f"se esperan entre 1 y 8 diapositivas, hay {len(filas)}"
    secciones_diap = " ".join(normal(f[1]) for f in filas)
    faltan = [clave for clave, _, _ in SECCIONES_ESPERADAS if clave not in secciones_diap]
    if faltan:
        return False, f"diapositivas no cubren secciones: {faltan}"
    return True, f"{len(filas)} diapositivas cubren las 5 secciones"


def demo_coincide(texto: str) -> tuple[bool, str]:
    import ensayo_demo  # import local para evitar ciclo con ensayo_demo.py

    listados = re.findall(r"^- (PASO-\d+) (.+)$", cuerpo_de(texto, "demo"), re.M)
    if not listados:
        return False, "la seccion Demo no lista pasos PASO-n"
    reales = [(p["id"], p["titulo"]) for p in ensayo_demo.PASOS]
    if len(listados) != len(reales):
        return False, f"el guion lista {len(listados)} pasos y la demo tiene {len(reales)}"
    for (id_g, t_g), (id_d, t_d) in zip(listados, reales):
        if id_g != id_d or normal(t_g) != normal(t_d):
            return False, f"{id_g} dice '{t_g}' y la demo '{t_d}'"
    return True, f"los {len(reales)} pasos coinciden con ensayo_demo.py"


def comprobar_guion9(texto: str) -> tuple[bool, str]:
    for marca in ("[COMPLETAR]", "TODO", "TBD"):
        if marca in texto:
            return False, f"contiene marcador pendiente: {marca}"
    if CLAVE_GOOGLE.search(texto) or ASIGNACION.search(texto):
        return False, "contiene texto con forma de secreto"
    return True, "sin pendientes; ninguna clave ni valor de secreto"


def verificar(texto: str | None = None, total_pruebas: int | None = None) -> list[tuple[str, str, bool, str]]:
    contenido = texto if texto is not None else GUION.read_text(encoding="utf-8")
    return [
        ("GUION-1", "secciones y tiempo", *comprobar_guion1(contenido)),
        ("GUION-2", "palabras", *comprobar_guion2(contenido)),
        ("GUION-3", "identificadores", *comprobar_guion3(contenido)),
        ("GUION-4", "riesgos mayores", *comprobar_guion4(contenido)),
        ("GUION-5", "cifras", *comprobar_guion5(contenido, total_pruebas=total_pruebas)),
        ("GUION-6", "tecnologias", *comprobar_guion6(contenido)),
        ("GUION-7", "diapositivas", *comprobar_guion7(contenido)),
        ("GUION-8", "demo", *demo_coincide(contenido)),
        ("GUION-9", "pendientes y secretos", *comprobar_guion9(contenido)),
    ]


def main() -> int:
    comprobaciones = verificar()
    ok_count = 0
    for codigo, nombre, ok, detalle in comprobaciones:
        marca = "PASA " if ok else "FALLA"
        print(f"{marca} {codigo} {nombre} -> {detalle}")
        if ok:
            ok_count += 1
    print(f"\n{ok_count} de {len(comprobaciones)} comprobaciones cumplidas")
    return 0 if ok_count == len(comprobaciones) else 1


if __name__ == "__main__":
    sys.exit(main())
