"""Resumen cuantitativo de cobertura y horas de la Ficha de Diseño Funcional (U3.1 · Bloque 34)."""
from __future__ import annotations

from ficha_datos import cargar


def main() -> None:
    ficha = cargar()
    cajones = ficha["cajones"]
    criterios = ficha["criterios"]
    hitos = ficha["hitos"]

    cubiertos_ca = {rid for c in criterios for rid in c["cubre"]}
    exigidos = cajones["Imprescindible"] + list(ficha["rnf"])
    sin_criterio = [rid for rid in exigidos if rid not in cubiertos_ca]

    ids_ca = {c["id"] for c in criterios}
    probados = {cid for h in hitos for cid in h["criterios"]}
    ca_huerfanos = sorted(ids_ca - probados)
    hitos_sin_ca = [h["id"] for h in hitos if not h["criterios"]]

    total_h = sum(h["horas"] for h in hitos)
    disp = ficha["disponibles"] or 0.0
    margen = ficha["margen"] or 0.0
    posibles = disp - margen

    print(f"RF: {len(ficha['rf'])} | RNF: {len(ficha['rnf'])}")
    print(
        f"Alcance: imprescindibles {len(cajones['Imprescindible'])}, "
        f"deseables {len(cajones['Deseable'])}, "
        f"fuera de alcance {len(cajones['Fuera de alcance'])}"
    )
    print(f"Criterios de aceptacion: {len(criterios)}")
    print(
        "Imprescindibles y RNF sin criterio:",
        ", ".join(sin_criterio) if sin_criterio else "ninguno",
    )
    print(
        f"Hitos: {len(hitos)} | Horas planificadas: {total_h:.1f} h de {posibles:.1f} h "
        f"posibles ({disp:.1f} h menos {margen:.1f} h de margen)"
    )
    print(
        "Criterios que ningun hito comprueba:",
        ", ".join(ca_huerfanos) if ca_huerfanos else "ninguno",
    )
    print(
        "Hitos sin criterio:",
        ", ".join(hitos_sin_ca) if hitos_sin_ca else "ninguno",
    )


if __name__ == "__main__":
    main()
