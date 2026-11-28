"""Verificador de la prueba de transferencia — reglas TRA-1 a TRA-6 (U3.6 · Bloque 45)."""
from __future__ import annotations

import re
import sys

import registrar_transferencia
from transferencia import CAUSAS_VALIDAS, ESTADOS_VALIDOS, META_MINUTOS, PRUEBA


def comprobar_tra1() -> tuple[bool, str]:
    tareas = PRUEBA.get("tareas", [])
    if len(tareas) < 5:
        return False, f"Se requieren >= 5 tareas, hay {len(tareas)}."
    no_logradas = [t["id"] for t in tareas if not t.get("lograda")]
    if no_logradas:
        return False, f"Tareas no logradas: {no_logradas}"
    return True, f"{len(tareas)} de {len(tareas)} tareas logradas."


def comprobar_tra2() -> tuple[bool, str]:
    mins = int(PRUEBA.get("duracion_minutos", 999))
    preguntas = int(PRUEBA.get("preguntas_al_autor", 999))
    if mins > META_MINUTOS:
        return False, f"Duración {mins} min excede meta de {META_MINUTOS} min."
    if preguntas != 0:
        return False, f"Se hicieron {preguntas} preguntas al autor (meta: 0)."
    return True, f"{mins} min (<= {META_MINUTOS}) y 0 preguntas al autor."


def comprobar_tra3() -> tuple[bool, str]:
    usados = set(PRUEBA.get("documentos_usados", []))
    esperados = {"README.md", "docs/api.md"}
    if not esperados.issubset(usados):
        return False, f"Faltan documentos base: {sorted(esperados - usados)}"
    return True, "Protocolo seguido usando README.md y docs/api.md."


def comprobar_tra4() -> tuple[bool, str]:
    obs = PRUEBA.get("observaciones", [])
    for o in obs:
        if o.get("causa") not in CAUSAS_VALIDAS:
            return False, f"{o.get('id')} causa inválida: {o.get('causa')}"
        if o.get("estado") not in ESTADOS_VALIDOS:
            return False, f"{o.get('id')} estado inválido: {o.get('estado')}"
        if len(str(o.get("accion", "")).strip()) < 20:
            return False, f"{o.get('id')} acción demasiado corta."
    return True, f"{len(obs)} observaciones clasificadas y cerradas."


def comprobar_tra5() -> tuple[bool, str]:
    for o in PRUEBA.get("observaciones", []):
        if o.get("causa") == "producto" and not o.get("limitacion"):
            return False, f"{o['id']} (causa=producto) no declara clave 'limitacion'."
    return True, "Observaciones de producto enlazadas a su limitación."


def comprobar_tra6() -> tuple[bool, str]:
    ruta = registrar_transferencia.DESTINO
    if not ruta.exists():
        return False, f"No existe {ruta.name}."
    texto = ruta.read_text(encoding="utf-8")
    esperada = registrar_transferencia.huella(PRUEBA)
    m = re.search(r"Huella de la prueba:\*{0,2}\s*([0-9a-f]{12})", texto)
    if not m:
        return False, f"{ruta.name} sin huella."
    if m.group(1) != esperada:
        return False, f"Huella desactualizada ({m.group(1)} != {esperada})."
    return True, f"{ruta.name} vigente con huella {esperada}."


def verificar() -> list[tuple[str, bool, str]]:
    return [
        ("TRA-1", *comprobar_tra1()),
        ("TRA-2", *comprobar_tra2()),
        ("TRA-3", *comprobar_tra3()),
        ("TRA-4", *comprobar_tra4()),
        ("TRA-5", *comprobar_tra5()),
        ("TRA-6", *comprobar_tra6()),
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
