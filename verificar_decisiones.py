"""Verificador de decisiones de arquitectura y limitaciones — reglas DEC-1 a DEC-7 (Core U3.6 · Bloque 45)."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import alucinaciones
import ataques
import matriz_modelo
import matriz_pruebas
import riesgos
import transferencia

REPO_ROOT = Path(__file__).resolve().parent
DECISIONES_MD = REPO_ROOT / "docs" / "decisiones.md"
LIMITACIONES_MD = REPO_ROOT / "docs" / "limitaciones.md"
README_MD = REPO_ROOT / "README.md"

CAMPOS_DECISION = ("Estado", "Contexto", "Decisión", "Alternativas descartadas", "Costo")
ESTADOS_DECISION = {"vigente", "reemplazada"}


def parsear_decisiones(texto: str) -> list[dict[str, Any]]:
    bloques = re.split(r"^##\s+(D-\d+)\s+[—-]\s+(.+)$", texto, flags=re.M)
    resultado: list[dict[str, Any]] = []
    for i in range(1, len(bloques), 3):
        did = bloques[i].strip()
        titulo = bloques[i + 1].strip()
        cuerpo = bloques[i + 2]
        campos: dict[str, str] = {}
        for campo in CAMPOS_DECISION:
            m = re.search(rf"^\-\s+\*\*{re.escape(campo)}:\*\*\s*(.+)$", cuerpo, re.M)
            if m:
                campos[campo] = m.group(1).strip()
        resultado.append({"id": did, "titulo": titulo, "campos": campos})
    return resultado


def parsear_limitaciones(texto: str) -> list[dict[str, str]]:
    filas: list[dict[str, str]] = []
    for linea in texto.splitlines():
        s = linea.strip()
        if not s.startswith("|") or not s.endswith("|"):
            continue
        celdas = [c.strip() for c in s.strip("|").split("|")]
        if len(celdas) == 6 and re.fullmatch(r"LIM-\d+", celdas[0]):
            filas.append(
                {
                    "id": celdas[0],
                    "que_no_hace": celdas[1],
                    "origen": celdas[2],
                    "riesgo": celdas[3],
                    "efecto": celdas[4],
                    "decision": celdas[5],
                }
            )
    return filas


def origenes_en_codigo() -> set[str]:
    origenes: set[str] = set()
    for a in ataques.ATAQUES:
        if isinstance(a.get("hallazgo"), dict) and a["hallazgo"].get("clasificacion") == "limitacion":
            origenes.add(a["id"])
    for s in alucinaciones.SONDAS:
        if not s.get("detectable", True):
            origenes.add(s["id"])
    for m in matriz_modelo.MATRIZ + matriz_pruebas.MATRIZ:
        if isinstance(m.get("hallazgo"), dict) and m["hallazgo"].get("clasificacion") == "limitacion":
            origenes.add(m["id"])
    return origenes


def comprobar_dec1(decisiones: list[dict[str, Any]]) -> tuple[bool, str]:
    if len(decisiones) < 5:
        return False, f"Se requieren >= 5 decisiones, hay {len(decisiones)}."
    for d in decisiones:
        faltan = [c for c in CAMPOS_DECISION if c not in d["campos"]]
        if faltan:
            return False, f"{d['id']} sin campos: {faltan}"
        if d["campos"]["Estado"].lower() not in ESTADOS_DECISION:
            return False, f"{d['id']} estado inválido: {d['campos']['Estado']}"
    return True, f"{len(decisiones)} decisiones completas con 5 campos y estado válido."


def comprobar_dec2(decisiones: list[dict[str, Any]]) -> tuple[bool, str]:
    for d in decisiones:
        for campo in ("Alternativas descartadas", "Costo"):
            if len(d["campos"].get(campo, "")) < 30:
                return False, f"{d['id']} tiene '{campo}' demasiado corto (<30 chars)."
    return True, "Todas las alternativas descartadas y costos tienen >= 30 caracteres."


def comprobar_dec3(decisiones: list[dict[str, Any]], readme: str) -> tuple[bool, str]:
    vigentes = [d["id"] for d in decisiones if d["campos"].get("Estado", "").lower() == "vigente"]
    faltan = [did for did in vigentes if did not in readme]
    if faltan:
        return False, f"README.md no cita las decisiones vigentes: {faltan}"
    for doc in ("docs/decisiones.md", "docs/limitaciones.md"):
        if doc not in readme:
            return False, f"README.md no enlaza {doc}."
    return True, f"README.md cita {vigentes} y enlaza decisiones y limitaciones."


def comprobar_dec4(limitaciones: list[dict[str, str]]) -> tuple[bool, str]:
    esperados = origenes_en_codigo()
    en_doc = {lim["origen"] for lim in limitaciones}
    if esperados != en_doc:
        return False, f"Desajuste de orígenes: código={sorted(esperados)} vs doc={sorted(en_doc)}"
    return True, f"Correspondencia exacta 1:1 de orígenes: {sorted(esperados)}."


def comprobar_dec5(limitaciones: list[dict[str, str]]) -> tuple[bool, str]:
    mapa_riesgos = {r["id"]: r for r in riesgos.RIESGOS}
    for lim in limitaciones:
        if len(lim["efecto"]) < 30 or len(lim["decision"]) < 30:
            return False, f"{lim['id']} tiene efecto o decisión < 30 caracteres."
        r = mapa_riesgos.get(lim["riesgo"])
        if not r:
            return False, f"{lim['id']} apunta a riesgo inexistente {lim['riesgo']}."
        if r["estado"] not in ("parcial", "aceptada"):
            return False, f"{lim['id']} apunta a {lim['riesgo']} con estado '{r['estado']}'."
        if lim["origen"] not in r.get("limites", []):
            return False, f"{lim['riesgo']} no lista origen {lim['origen']} en 'limites'."
    return True, f"{len(limitaciones)} limitaciones trazadas a riesgos parciales/aceptados."


def comprobar_dec6(limitaciones: list[dict[str, str]], readme: str) -> tuple[bool, str]:
    ids = [lim["id"] for lim in limitaciones]
    faltan = [lid for lid in ids if lid not in readme]
    if faltan:
        return False, f"README.md no cita las limitaciones: {faltan}"
    return True, f"README.md cita todas las limitaciones: {ids}."


def comprobar_dec7(limitaciones: list[dict[str, str]]) -> tuple[bool, str]:
    ids_validos = {lim["id"] for lim in limitaciones}
    for obs in transferencia.PRUEBA.get("observaciones", []):
        if obs.get("causa") == "producto":
            lid = obs.get("limitacion")
            if lid not in ids_validos:
                return False, f"Observación {obs['id']} (producto) apunta a limitación inválida {lid!r}."
    return True, "Observaciones de producto en transferencia.py enlazadas a LIM-NN válido."


def verificar() -> list[tuple[str, bool, str]]:
    dec_txt = DECISIONES_MD.read_text(encoding="utf-8")
    lim_txt = LIMITACIONES_MD.read_text(encoding="utf-8")
    readme_txt = README_MD.read_text(encoding="utf-8")
    decisiones = parsear_decisiones(dec_txt)
    limitaciones = parsear_limitaciones(lim_txt)
    return [
        ("DEC-1", *comprobar_dec1(decisiones)),
        ("DEC-2", *comprobar_dec2(decisiones)),
        ("DEC-3", *comprobar_dec3(decisiones, readme_txt)),
        ("DEC-4", *comprobar_dec4(limitaciones)),
        ("DEC-5", *comprobar_dec5(limitaciones)),
        ("DEC-6", *comprobar_dec6(limitaciones, readme_txt)),
        ("DEC-7", *comprobar_dec7(limitaciones)),
    ]


def main() -> int:
    comprobaciones = verificar()
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
