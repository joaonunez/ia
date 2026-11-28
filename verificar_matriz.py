"""Verificador de la Matriz de Pruebas — reglas MAT-1 a MAT-6 (U3.5 · Bloque 42)."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import ejecutar_matriz

REPO_ROOT = Path(__file__).resolve().parent
FICHA = REPO_ROOT / "docs" / "ficha_diseno_funcional.md"
CLAVES_OBLIGATORIAS = {"id", "tipo", "escenario", "peticion", "esperado", "cubre"}
TIPOS_ESPERADOS = {"valido", "invalido", "borde"}


def _imprescindibles_ficha() -> set[str]:
    texto = FICHA.read_text(encoding="utf-8")
    for linea in texto.splitlines():
        if linea.strip().startswith("Imprescindible:"):
            return set(re.findall(r"RF-\d+", linea))
    return set()


def comprobar_mat1(matriz: list[dict[str, Any]]) -> tuple[bool, str]:
    if len(matriz) < 4:
        return False, f"Se requieren >= 4 escenarios, hay {len(matriz)}."
    ids = [c.get("id") for c in matriz]
    if len(ids) != len(set(ids)):
        return False, "Hay IDs duplicados en la matriz."
    tipos = set()
    for caso in matriz:
        faltan = CLAVES_OBLIGATORIAS - set(caso.keys())
        if faltan:
            return False, f"{caso.get('id', '?')} sin claves: {sorted(faltan)}"
        tipos.add(caso["tipo"])
    faltan_tipos = TIPOS_ESPERADOS - tipos
    if faltan_tipos:
        return False, f"Faltan tipos de escenario: {sorted(faltan_tipos)}"
    return True, f"{len(matriz)} escenarios válidos con IDs únicos y los 3 tipos."


def comprobar_mat2(matriz: list[dict[str, Any]]) -> tuple[bool, str]:
    for caso in matriz:
        esp = caso.get("esperado", {})
        if "estado" not in esp:
            return False, f"{caso['id']} no declara estado esperado."
        if "contiene" not in esp and "fuentes" not in esp:
            return False, f"{caso['id']} solo valida HTTP sin 'contiene' ni 'fuentes'."
    return True, "Todos los escenarios verifican estado HTTP y contenido o fuentes."


def comprobar_mat3(matriz: list[dict[str, Any]]) -> tuple[bool, str]:
    requeridos = _imprescindibles_ficha()
    if not requeridos:
        return False, "No se encontraron códigos RF en Imprescindible: de la ficha."
    cubiertos: set[str] = set()
    for caso in matriz:
        cubiertos.update(caso.get("cubre", []))
    faltan = sorted(requeridos - cubiertos)
    if faltan:
        return False, f"Faltan requerimientos imprescindibles: {faltan}"
    return True, f"Trazabilidad completa sobre {sorted(requeridos)}."


def comprobar_mat4(nombre_modulo: str, matriz: list[dict[str, Any]]) -> tuple[bool, str]:
    ruta = ejecutar_matriz.registro_de(nombre_modulo)
    if not ruta.exists():
        return False, f"No existe el registro {ruta.name}."
    texto = ruta.read_text(encoding="utf-8")
    esperada = ejecutar_matriz.huella(matriz)
    m = re.search(r"Huella de la matriz:\*{0,2}\s*([0-9a-f]{12})", texto)
    if not m:
        return False, f"{ruta.name} no contiene 'Huella de la matriz: <12-hex>'."
    if m.group(1) != esperada:
        return False, f"Huella desactualizada ({m.group(1)} != {esperada})."
    return True, f"{ruta.name} vigente con huella {esperada}."


def comprobar_mat5(resultados: list[dict[str, Any]]) -> tuple[bool, str]:
    for r in resultados:
        if r["resultado"] == "FALLA":
            h = r.get("hallazgo")
            if not isinstance(h, dict):
                return False, f"{r['id']} falló sin hallazgo declarado."
            if h.get("clasificacion") != "limitacion":
                return False, f"{r['id']} tiene clasificación '{h.get('clasificacion')}' abierta."
            if len(str(h.get("decision", "")).strip()) < 20:
                return False, f"{r['id']} tiene decisión demasiado corta (<20 caracteres)."
    return True, "Sin defectos ni fallas sin clasificar abiertas."


def comprobar_mat6(resultados: list[dict[str, Any]]) -> tuple[bool, str]:
    errores_5xx = [r["id"] for r in resultados if int(r["estado"]) >= 500]
    if errores_5xx:
        return False, f"Respuestas 5xx detectadas en: {errores_5xx}"
    return True, "0 respuestas 5xx en toda la matriz."


def verificar(nombre_modulo: str = "matriz_pruebas", url: str | None = None) -> list[tuple[str, bool, str]]:
    matriz = ejecutar_matriz.cargar(nombre_modulo)
    resultados = ejecutar_matriz.ejecutar(matriz, url=url)
    return [
        ("MAT-1", *comprobar_mat1(matriz)),
        ("MAT-2", *comprobar_mat2(matriz)),
        ("MAT-3", *comprobar_mat3(matriz)),
        ("MAT-4", *comprobar_mat4(nombre_modulo, matriz)),
        ("MAT-5", *comprobar_mat5(resultados)),
        ("MAT-6", *comprobar_mat6(resultados)),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica reglas MAT-1 a MAT-6.")
    parser.add_argument("--matriz", default="matriz_pruebas")
    parser.add_argument("--url", default=None)
    args = parser.parse_args()

    comprobaciones = verificar(args.matriz, url=args.url)
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
