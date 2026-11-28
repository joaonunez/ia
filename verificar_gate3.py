"""Calcula el puntaje del Gate 3 con la evidencia real del proyecto (U3.7 · Bloque S2).

Uso:
    python verificar_gate3.py               # sin Docker: PROVISIONAL
    python verificar_gate3.py --con-docker  # incluye stack, ejecucion y registro
    python verificar_gate3.py --escribir    # guarda docs/gate3.md
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any

from rubrica_gate3 import CRITERIOS, ENTREGABLES, NO_COMPENSABLES, UMBRAL

REPO_ROOT = Path(__file__).resolve().parent
INFORME = REPO_ROOT / "docs" / "gate3.md"
TOPE_DE_UNA_FUENTE = 300
PY = sys.executable

IA = [
    "tests/parciales/" + n
    for n in (
        "test_cadena.py",
        "test_fundamentacion.py",
        "test_modelo.py",
        "test_respaldo.py",
        "test_recuperar.py",
        "test_prompt.py",
    )
]

# fuente -> (orden, requiere Docker)
FUENTES: dict[str, tuple[list[str], bool]] = {
    "ficha": ([PY, "verificar_ficha_completa.py"], False),
    "decisiones": ([PY, "verificar_decisiones.py"], False),
    "frio": ([PY, "probar_en_frio.py"], False),
    "demo": ([PY, "ensayo_demo.py"], False),
    "respaldo": ([PY, "ensayo_demo.py", "--comprobar"], False),
    "mitigaciones": ([PY, "verificar_mitigaciones.py"], False),
    "ia": ([PY, "-m", "pytest", "-q", *IA], False),
    "servicio": ([PY, "verificar_servicio.py"], False),
    "api_md": ([PY, "generar_api_md.py", "--comprobar"], False),
    "dockerfile": ([PY, "verificar_dockerfile.py"], False),
    "compose": ([PY, "verificar_entrega.py"], False),
    "pytest": ([PY, "-m", "pytest", "-q"], False),
    "matriz": ([PY, "verificar_matriz.py"], False),
    "parciales": ([PY, "verificar_parciales.py"], False),
    "riesgos": ([PY, "verificar_riesgos.py"], False),
    "secretos": ([PY, "buscar_secretos.py"], False),
    "readme": ([PY, "verificar_readme.py"], False),
    "transferencia": ([PY, "verificar_transferencia.py"], False),
    "guion": ([PY, "medir_guion.py"], False),
    "stack": ([PY, "verificar_stack.py"], True),
    "ejecucion": ([PY, "verificar_ejecucion.py"], True),
    "registro": ([PY, "verificar_registro.py"], True),
}

LIMITES_DEL_INFORME = [
    "Que la presentacion se haya construido: solo se mide el guion.",
    "Que el tiempo de la demo sea el de una persona real: es una estimacion con 130 palabras por minuto.",
    "Que los criterios no compensables sean los definitivos: son una propuesta del equipo de diseno instruccional que el validador debe confirmar.",
    "Lo que solo confirma el evaluador (ver la seccion anterior).",
    "Lo que viva en los contenedores, si el modo fue sin Docker.",
]

CUMPLIDAS = re.compile(r"(\d+) de (\d+) (?:comprobaciones|reglas|pasos)")


def cifras_de_pytest(salida: str) -> tuple[int, int]:
    cuentas: dict[str, int] = {}
    for clave in ("passed", "failed", "error"):
        hallados = re.findall(rf"(\d+) {clave}", salida)
        cuentas[clave] = sum(int(n) for n in hallados)
    return cuentas["passed"], sum(cuentas.values())


def leer_cifras(salida: str, codigo: int, es_pytest: bool = False) -> tuple[int, int]:
    """(cumplidas, total) de lo que imprime un verificador."""
    if es_pytest:
        cumplidas, total = cifras_de_pytest(salida)
        if total:
            return cumplidas, total
    vistas = CUMPLIDAS.findall(salida)
    if vistas:
        cumplidas, total = map(int, vistas[-1])
        if codigo != 0 and cumplidas == total:
            total += 1
        return cumplidas, total
    return (1, 1) if codigo == 0 else (0, 1)


def primera_causa(salida: str, codigo: int) -> str:
    """La primera línea que explica un fallo, ya sin sangrías."""
    lineas = salida.splitlines()
    for i, linea in enumerate(lineas):
        if linea.startswith(("FALLA", "FAILED", "[FAIL]")):
            causa = [linea.split(" ", 1)[1].strip()]
            for siguiente in lineas[i + 1 :]:
                if not siguiente.startswith(" "):
                    break
                causa.append(siguiente.strip())
            return " ".join(causa)
    utiles = [ln.strip() for ln in lineas if ln.strip()]
    return utiles[-1] if codigo != 0 and utiles else ""


def correr_fuente(nombre: str) -> tuple[int, int, str]:
    """(cumplidas, total, causa del primer fallo o cadena vacía)."""
    orden, _ = FUENTES[nombre]
    try:
        r = subprocess.run(
            orden,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={**os.environ, "PYTHONUTF8": "1"},
            timeout=TOPE_DE_UNA_FUENTE,
        )
    except subprocess.TimeoutExpired:
        return 0, 1, f"tardo mas de {TOPE_DE_UNA_FUENTE} s"
    salida = r.stdout + r.stderr
    cumplidas, total = leer_cifras(salida, r.returncode, "pytest" in orden)
    causa = primera_causa(salida, r.returncode)
    return cumplidas, total, causa if cumplidas != total else ""


def puntuar(resultados: dict[str, tuple[int, int]]) -> list[tuple[dict[str, Any], float, str]]:
    """[(criterio, puntos, evidencia)] con la media por fuente."""
    filas = []
    for c in CRITERIOS:
        usadas = [f for f in c["fuentes"] if f in resultados]
        if not usadas:
            filas.append((c, 0.0, "sin evidencia"))
            continue
        fracciones = [resultados[f][0] / resultados[f][1] for f in usadas]
        puntos = c["peso"] * sum(fracciones) / len(fracciones)
        evidencia = ", ".join(f"{f} {resultados[f][0]}/{resultados[f][1]}" for f in usadas)
        filas.append((c, puntos, evidencia))
    return filas


def no_compensables_que_fallan(
    resultados: dict[str, tuple[int, int]]
) -> list[tuple[dict[str, Any], str]]:
    fallan = []
    for nc in NO_COMPENSABLES:
        if not nc["fuentes"]:
            continue
        usadas = [f for f in nc["fuentes"] if f in resultados]
        rotas = [f for f in usadas if resultados[f][0] != resultados[f][1]]
        if not usadas:
            fallan.append((nc, "sin evidencia"))
        elif rotas:
            fallan.append((nc, "falla " + ", ".join(rotas)))
    return fallan


def decidir(
    puntaje: float,
    fallan: list[tuple[dict[str, Any], str]],
    omitidas: list[str],
) -> tuple[str, str]:
    if fallan:
        return "NO APRUEBA", "un criterio no compensable falla"
    if puntaje < UMBRAL:
        return "NO APRUEBA", f"el puntaje no llega a {UMBRAL}"
    if omitidas:
        return "PROVISIONAL", "faltan las comprobaciones con Docker: " + ", ".join(omitidas)
    return "APRUEBA", f"puntaje de al menos {UMBRAL} y nada que falle"


def nota(puntaje: float) -> float:
    """Nota de 1.0 a 7.0 con 60 % de exigencia: UMBRAL puntos dan 4.0."""
    if puntaje < UMBRAL:
        return 1.0 + 3.0 * puntaje / UMBRAL
    return 4.0 + 3.0 * (puntaje - UMBRAL) / (100 - UMBRAL)


def confirma_el_evaluador() -> list[tuple[str, str]]:
    return [(nc["id"], nc["evaluador"]) for nc in NO_COMPENSABLES if "evaluador" in nc]


def entregables_que_faltan(raiz: Path = REPO_ROOT) -> list[tuple[str, list[str]]]:
    faltan = []
    for nombre, archivos in ENTREGABLES:
        ausentes = [a for a in archivos if not (raiz / a).is_file()]
        if ausentes:
            faltan.append((nombre, ausentes))
    return faltan


def huella(resultados: dict[str, tuple[int, int]]) -> str:
    texto = json.dumps(resultados, sort_keys=True)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def informe(
    modo: str,
    resultados: dict[str, tuple[int, int]],
    filas: list[tuple[dict[str, Any], float, str]],
    puntaje: float,
    fallan: list[tuple[dict[str, Any], str]],
    veredicto: tuple[str, str],
) -> str:
    rotos = {nc["id"]: motivo for nc, motivo in fallan}
    lineas = [
        "# Informe del Gate 3",
        "",
        f"Fecha: {datetime.date.today().isoformat()}",
        f"Modo: {modo}",
        f"Huella de la evidencia: {huella(resultados)}",
        f"Puntaje: {puntaje:.1f} de 100 (umbral {UMBRAL})",
        f"Nota: {nota(puntaje):.1f} (escala 1 a 7; {UMBRAL} puntos dan 4.0)",
        f"Resultado: {veredicto[0]}",
        "",
        "## Criterios",
        "",
        "| ID | Criterio | Peso | Puntos | Evidencia |",
        "|----|----------|------|--------|-----------|",
    ]
    for c, puntos, evidencia in filas:
        lineas.append(f"| {c['id']} | {c['nombre']} | {c['peso']} | {puntos:.1f} | {evidencia} |")

    lineas += [
        "",
        "## No compensables",
        "",
        "| ID | Criterio | Estado |",
        "|----|----------|--------|",
    ]
    for nc in NO_COMPENSABLES:
        sin_programa = "cumple" if nc["fuentes"] else "lo confirma el evaluador"
        estado = rotos.get(nc["id"], sin_programa)
        lineas.append(f"| {nc['id']} | {nc['nombre']} | {estado} |")

    lineas += [
        "",
        "## Lo que confirma el evaluador",
        "",
        "| ID | Que confirma |",
        "|----|--------------|",
    ]
    for id_, que in confirma_el_evaluador():
        lineas.append(f"| {id_} | {que} |")

    lineas += [
        "",
        "## Entregables",
        "",
        "| Entregable | Archivos |",
        "|------------|----------|",
    ]
    for nombre, archivos in ENTREGABLES:
        lineas.append(f"| {nombre} | {', '.join(archivos)} |")

    lineas += ["", "## Lo que este informe no demuestra", ""]
    lineas += [f"- {limite}" for limite in LIMITES_DEL_INFORME]
    return "\n".join(lineas) + "\n"


def imprimir(marca: str, nombre: str, detalle: str) -> None:
    linea = f"{marca} {nombre} {detalle}"
    print(textwrap.fill(linea, 78, subsequent_indent="      "))


def bajar() -> None:
    subprocess.run(
        ["docker", "compose", "down"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def levantar() -> str:
    r = subprocess.run(
        ["docker", "compose", "up", "-d", "--build", "--wait", "--wait-timeout", "120"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if r.returncode == 0:
        return ""
    lineas = [x for x in (r.stdout + r.stderr).splitlines() if x.strip()]
    return lineas[-1][:150] if lineas else "sin mensaje"


def _correr(
    con_docker: bool,
    resultados: dict[str, tuple[int, int]],
    omitidas: list[str],
) -> None:
    for nombre, (_, docker) in FUENTES.items():
        if docker and not con_docker:
            omitidas.append(nombre)
            imprimir("OMITE", nombre, "-> requiere Docker")
            continue
        cumplidas, total, causa = correr_fuente(nombre)
        resultados[nombre] = (cumplidas, total)
        marca = "PASA " if cumplidas == total else "FALLA"
        detalle = f"-> {cumplidas} de {total}"
        if causa:
            detalle += f": {causa}"
        imprimir(marca, nombre, detalle)
        if con_docker and nombre == "stack":
            causa_up = levantar()
            if causa_up:
                imprimir("FALLA", "levantar", "-> " + causa_up)


def correr_todas(con_docker: bool) -> tuple[dict[str, tuple[int, int]], list[str]]:
    resultados: dict[str, tuple[int, int]] = {}
    omitidas: list[str] = []
    if con_docker:
        bajar()
    try:
        _correr(con_docker, resultados, omitidas)
    finally:
        if con_docker:
            bajar()
    return resultados, omitidas


def main(argumentos: list[str] | None = None) -> int:
    args = argumentos if argumentos is not None else sys.argv[1:]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    con_docker = "--con-docker" in args
    faltan = entregables_que_faltan()
    if faltan:
        for nombre, ausentes in faltan:
            imprimir("FALTA", nombre, "-> " + ", ".join(ausentes))
        print(f"\n{len(faltan)} de {len(ENTREGABLES)} entregables incompletos: no hay nada que evaluar")
        return 1

    resultados, omitidas = correr_todas(con_docker)
    filas = puntuar(resultados)
    puntaje = sum(p for _, p, _ in filas)
    print()
    for c, puntos, _ in filas:
        print(f"{c['id']} {c['nombre']:<40} {puntos:>4.1f} / {c['peso']}")
    print(f"\nPuntaje: {puntaje:.1f} de 100 (umbral {UMBRAL})")
    print(f"Nota: {nota(puntaje):.1f} (escala 1 a 7; {UMBRAL} puntos dan 4.0)")

    fallan = no_compensables_que_fallan(resultados)
    rotos = {nc["id"]: motivo for nc, motivo in fallan}
    for nc in NO_COMPENSABLES:
        if not nc["fuentes"]:
            continue
        motivo = rotos.get(nc["id"])
        detalle = nc["nombre"] + (f" -> {motivo}" if motivo else "")
        imprimir("FALLA" if motivo else "PASA ", nc["id"], detalle)
    for id_, que in confirma_el_evaluador():
        imprimir("EVALUA", id_, "-> " + que)

    veredicto = decidir(puntaje, fallan, omitidas)
    print()
    imprimir("Resultado:", veredicto[0], f"({veredicto[1]})")

    if "--escribir" in args:
        modo = "con Docker" if con_docker else "sin Docker"
        texto = informe(modo, resultados, filas, puntaje, fallan, veredicto)
        INFORME.parent.mkdir(parents=True, exist_ok=True)
        INFORME.write_text(texto, encoding="utf-8")
        print(f"escrito {INFORME}")

    return {"APRUEBA": 0, "PROVISIONAL": 2}.get(veredicto[0], 1)


if __name__ == "__main__":
    sys.exit(main())
