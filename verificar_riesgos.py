"""Verificador de la Matriz de Riesgos — reglas RIE-1 a RIE-6 (Core U3.5 · Bloque 43)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import alucinaciones
import ataques
import ejecutar_matriz
import matriz_modelo
import matriz_pruebas
import riesgos
import verificar_mitigaciones

REPO_ROOT = Path(__file__).resolve().parent
CLAVES_OBLIGATORIAS = {
    "id",
    "riesgo",
    "probabilidad",
    "impacto",
    "mitigacion",
    "evidencia",
    "estado",
    "residual",
}


def _limites_declarados_en_codigo() -> set[str]:
    """Descubre todas las limitaciones declaradas en ataques, sondas y matriz_modelo."""
    limites: set[str] = set()
    for a in ataques.ATAQUES:
        h = a.get("hallazgo")
        if isinstance(h, dict) and h.get("clasificacion") == "limitacion":
            limites.add(a["id"])
    for s in alucinaciones.SONDAS:
        if not s.get("detectable", True):
            limites.add(s["id"])
    for m in matriz_modelo.MATRIZ:
        h = m.get("hallazgo")
        if isinstance(h, dict) and h.get("clasificacion") == "limitacion":
            limites.add(m["id"])
    return limites


def resolver(evidencia: str, _cache: dict[str, Any] | None = None) -> tuple[str, str]:
    """Ejecuta una evidencia tipada y devuelve `(estado, detalle)` (`PASA` | `LIMITE` | `FALLA`)."""
    cache = _cache if _cache is not None else {}
    if evidencia in cache:
        return cache[evidencia]

    prefijo, sep, objetivo = evidencia.partition(":")
    if not sep or not objetivo:
        res = ("FALLA", f"formato de evidencia inválido: {evidencia!r}")
        cache[evidencia] = res
        return res

    if prefijo == "ataques":
        mapa_a = {c["id"]: c for c in ataques.ATAQUES}
        mapa_b = {c["id"]: c for c in ataques.LEGITIMAS}
        if objetivo in mapa_a:
            r = verificar_mitigaciones.evaluar_ataque(mapa_a[objetivo])
            res = (r["estado"], r["detalle"])
        elif objetivo in mapa_b:
            r = verificar_mitigaciones.evaluar_legitima(mapa_b[objetivo])
            res = (r["estado"], r["detalle"])
        else:
            res = ("FALLA", f"ataque/legítima desconocido: {objetivo}")

    elif prefijo == "fuga":
        if "_fugas" not in cache:
            cache["_fugas"] = {r["id"]: r for r in verificar_mitigaciones.evaluar_fugas()}
        r = cache["_fugas"].get(objetivo)
        res = (r["estado"], r["detalle"]) if r else ("FALLA", f"fuga desconocida: {objetivo}")

    elif prefijo == "alucinacion":
        mapa_h = {s["id"]: s for s in alucinaciones.SONDAS}
        if objetivo in mapa_h:
            r = verificar_mitigaciones.evaluar_alucinacion(mapa_h[objetivo])
            res = (r["estado"], r["detalle"])
        else:
            res = ("FALLA", f"sonda desconocida: {objetivo}")

    elif prefijo in ("matriz", "matriz_modelo"):
        clave_cache = f"_mat_{prefijo}"
        if clave_cache not in cache:
            mod = matriz_pruebas.MATRIZ if prefijo == "matriz" else matriz_modelo.MATRIZ
            cache[clave_cache] = {r["id"]: r for r in ejecutar_matriz.ejecutar(mod)}
        r = cache[clave_cache].get(objetivo)
        if not r:
            res = ("FALLA", f"escenario {objetivo} no existe en {prefijo}")
        elif r["resultado"] == "PASA":
            res = ("PASA", f"HTTP {r['estado']}")
        elif isinstance(r.get("hallazgo"), dict) and r["hallazgo"].get("clasificacion") == "limitacion":
            res = ("LIMITE", "; ".join(r["motivos"]))
        else:
            res = ("FALLA", "; ".join(r["motivos"]))

    elif prefijo == "pruebas":
        ruta = REPO_ROOT / objetivo
        if not ruta.exists():
            res = ("FALLA", f"no existe {objetivo}")
        else:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", str(ruta)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
            res = ("PASA", "pytest ok") if proc.returncode == 0 else ("FALLA", proc.stdout.strip() or proc.stderr.strip())

    elif prefijo == "comando":
        ruta = REPO_ROOT / objetivo
        if not ruta.exists():
            res = ("FALLA", f"no existe {objetivo}")
        else:
            proc = subprocess.run(
                [sys.executable, str(ruta)],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=60,
            )
            res = ("PASA", "exit 0") if proc.returncode == 0 else ("FALLA", proc.stdout.strip() or proc.stderr.strip())

    else:
        res = ("FALLA", f"prefijo de evidencia no soportado: {prefijo!r}")

    cache[evidencia] = res
    return res


def comprobar_rie1(lista: list[dict[str, Any]]) -> tuple[bool, str]:
    if len(lista) < 6:
        return False, f"Se requieren >= 6 riesgos, hay {len(lista)}."
    ids = [r.get("id") for r in lista]
    if len(ids) != len(set(ids)):
        return False, "Hay IDs de riesgo duplicados."
    for r in lista:
        faltan = CLAVES_OBLIGATORIAS - set(r.keys())
        if faltan:
            return False, f"{r.get('id', '?')} sin claves: {sorted(faltan)}"
        if not (1 <= int(r["probabilidad"]) <= 5 and 1 <= int(r["impacto"]) <= 5):
            return False, f"{r['id']} tiene probabilidad/impacto fuera de 1..5."
        if r["estado"] not in riesgos.ESTADOS_VALIDOS:
            return False, f"{r['id']} tiene estado inválido: {r['estado']!r}."
        if not r["evidencia"]:
            return False, f"{r['id']} no declara evidencias."
    return True, f"{len(lista)} riesgos con estructura completa y válida."


def comprobar_rie2(lista: list[dict[str, Any]]) -> tuple[bool, str]:
    for r in lista:
        inh = riesgos.inherente(r)
        res = int(r["residual"])
        if r["estado"] == "aceptada":
            if res != inh:
                return False, f"{r['id']} aceptada debe mantener residual == inherente ({res} != {inh})."
        else:
            if not (1 <= res < inh):
                return False, f"{r['id']} ({r['estado']}) debe tener 1 <= residual < inherente ({res} vs {inh})."
    return True, "Coherencia verificada entre puntaje inherente, estado y residual."


def comprobar_rie3(lista: list[dict[str, Any]]) -> tuple[bool, str]:
    cache: dict[str, Any] = {}
    total = 0
    for r in lista:
        limites_r = set(r.get("limites", []))
        for ev in r["evidencia"]:
            total += 1
            estado, detalle = resolver(ev, cache)
            objetivo = ev.partition(":")[2]
            if estado == "PASA":
                continue
            if estado == "LIMITE" and objetivo in limites_r:
                continue
            return False, f"{r['id']} evidencia {ev} -> {estado} ({detalle})"
    return True, f"Todas las {total} evidencias ejecutadas y coherentes con su estado."


def comprobar_rie4(lista: list[dict[str, Any]]) -> tuple[bool, str]:
    esperados = _limites_declarados_en_codigo()
    cubiertos: set[str] = set()
    for r in lista:
        lims = r.get("limites", [])
        if lims:
            if len(str(r.get("nota", "")).strip()) < 20:
                return False, f"{r['id']} declara límites {lims} pero nota tiene < 20 caracteres."
            cubiertos.update(lims)
    faltan = sorted(esperados - cubiertos)
    if faltan:
        return False, f"Limitaciones del código sin cubrir en riesgos.py: {faltan}"
    return True, f"Todas las limitaciones del código cubiertas: {sorted(esperados)}."


def comprobar_rie5(lista: list[dict[str, Any]]) -> tuple[bool, str]:
    altos = []
    for r in lista:
        cat = riesgos.categoria(int(r["residual"]))
        if cat in ("ALTO", "CRITICO"):
            altos.append(r["id"])
            if len(str(r.get("supervision", "")).strip()) < 20:
                return False, f"{r['id']} es residual {cat} sin supervisión humana concreta (>=20 chars)."
    return True, f"Supervisión humana concreta verificada para residuales ALTO/CRITICO: {altos}."


def comprobar_rie6(lista: list[dict[str, Any]]) -> tuple[bool, str]:
    ruta = riesgos.DESTINO
    if not ruta.exists():
        return False, f"No existe {ruta.name}."
    texto = ruta.read_text(encoding="utf-8")
    esperada = riesgos.huella(lista)
    m = re.search(r"Huella de la matriz:\*{0,2}\s*([0-9a-f]{12})", texto)
    if not m:
        return False, f"{ruta.name} no contiene 'Huella de la matriz: <12-hex>'."
    if m.group(1) != esperada:
        return False, f"Huella desactualizada en {ruta.name} ({m.group(1)} != {esperada})."
    return True, f"{ruta.name} vigente con huella {esperada}."


def verificar() -> list[tuple[str, bool, str]]:
    lista = riesgos.RIESGOS
    return [
        ("RIE-1", *comprobar_rie1(lista)),
        ("RIE-2", *comprobar_rie2(lista)),
        ("RIE-3", *comprobar_rie3(lista)),
        ("RIE-4", *comprobar_rie4(lista)),
        ("RIE-5", *comprobar_rie5(lista)),
        ("RIE-6", *comprobar_rie6(lista)),
    ]


def main() -> int:
    comprobaciones = verificar()
    ok_count = 0
    for codigo, ok, detalle in comprobaciones:
        marca = "OK  " if ok else "FAIL"
        print(f"[{marca}] {codigo}: {detalle}")
        if ok:
            ok_count += 1
    print(f"Resultado: {ok_count} de {len(comprobaciones)} reglas cumplidas.")
    return 0 if ok_count == len(comprobaciones) else 1


if __name__ == "__main__":
    sys.exit(main())
