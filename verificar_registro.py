"""Verifica el registro de la ejecución completa `docs/registro_ejecucion.md` (U3.4 · Bloque 41)."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from buscar_secretos import ASIGNACION, CLAVE_GOOGLE
from escenarios import ESCENARIOS

REGISTRO = Path("docs/registro_ejecucion.md")
INICIO, FIN = "<!-- AUTO:INICIO -->", "<!-- AUTO:FIN -->"
SECCIONES = ["Qué se observó", "Qué no se probó", "Siguiente paso"]
MINIMO_CARACTERES = 40
COMMIT = re.compile(r"\| Commit del código \| ([0-9a-f]{7,40}) \(([^)]*)\) \|")
CIFRA = re.compile(r"Escenarios: (\d+) de (\d+) cumplidos")
FILA = re.compile(r"^\| (E-\d+) \| [^|]+ \| ([^|]+) \|$", re.M)
PRUEBAS = re.compile(r"Pruebas automáticas: (\d+) pasan, (\d+) fallan")


def leer(raiz: Path = Path(".")) -> str | None:
    archivo = raiz / REGISTRO
    if not archivo.exists():
        return None
    return archivo.read_text(encoding="utf-8")


def seccion(texto: str, titulo: str) -> str | None:
    patron = rf"^## {re.escape(titulo)}\n(.*?)(?=^## |\Z)"
    m = re.search(patron, texto, re.M | re.S)
    return m.group(1).strip() if m else None


def git(*args: str, raiz: Path = Path(".")) -> tuple[int, str]:
    r = subprocess.run(["git", "-C", str(raiz), *args], capture_output=True, text=True, check=False)
    return r.returncode, r.stdout.strip()


def estructura(texto: str) -> tuple[bool, str]:
    if INICIO not in texto or FIN not in texto:
        return False, "faltan las marcas AUTO:INICIO / AUTO:FIN"
    faltan = [s for s in SECCIONES if seccion(texto, s) is None]
    if faltan:
        return False, f"faltan las secciones {faltan}"
    return True, "zona automática y tres secciones manuales"


def manual_completo(texto: str) -> tuple[bool, str]:
    problemas: list[str] = []
    for titulo in SECCIONES:
        cuerpo = seccion(texto, titulo) or ""
        if "[COMPLETAR]" in cuerpo:
            problemas.append(f"'{titulo}' sigue sin completar")
        elif len(cuerpo) < MINIMO_CARACTERES:
            problemas.append(f"'{titulo}' es demasiado breve")
    if problemas:
        return False, "; ".join(problemas)
    return True, "las tres secciones están escritas"


def commit_vigente(texto: str, raiz: Path = Path(".")) -> tuple[bool, str]:
    m = COMMIT.search(texto)
    if not m:
        return False, "el registro no trae un commit del código"
    hash_, estado = m.groups()
    if estado != "sin cambios":
        return False, f"se ejecutó {estado}"
    codigo, _ = git("cat-file", "-e", f"{hash_}^{{commit}}", raiz=raiz)
    if codigo != 0:
        return False, f"el commit {hash_} no existe en este repositorio"
    _, cambios = git("diff", "--name-only", hash_, "HEAD", raiz=raiz)
    de_codigo = [f for f in cambios.splitlines() if not f.startswith("docs/")]
    if de_codigo:
        return False, f"el código cambió después de {hash_}: {de_codigo[:3]}"
    return True, f"{hash_} sigue siendo el código actual"


def cifras_coherentes(texto: str) -> tuple[bool, str]:
    m, p = CIFRA.search(texto), PRUEBAS.search(texto)
    if not (m and p):
        return False, "faltan las cifras de escenarios o de pruebas"
    cumplidos, total = int(m.group(1)), int(m.group(2))
    filas = FILA.findall(texto)
    pasan = sum(1 for _, r in filas if r.strip() == "pasa")
    problemas: list[str] = []
    if total != len(ESCENARIOS):
        problemas.append(f"dice {total} escenarios y escenarios.py tiene {len(ESCENARIOS)}")
    if (len(filas), pasan) != (total, cumplidos):
        problemas.append(f"la tabla suma {pasan} de {len(filas)}, la cifra dice {cumplidos} de {total}")
    if int(p.group(2)) != 0:
        problemas.append(f"hay {p.group(2)} pruebas que fallan")
    if problemas:
        return False, "; ".join(problemas)
    return True, f"{cumplidos} de {total}; {p.group(1)} pruebas pasan"


def respaldos_declarados(texto: str) -> tuple[bool, str]:
    m = re.search(r"\| ([^|]+) \| respaldo \|", texto)
    if not m:
        return True, "no se usó ningún respaldo"
    componente = m.group(1).strip()
    limites = seccion(texto, "Qué no se probó") or ""
    falta = [p for p in (componente.lower(), "respaldo") if p not in limites.lower()]
    if falta:
        return False, f"'{componente}' corrió con respaldo y 'Qué no se probó' no nombra {falta}"
    return True, f"'{componente}' con respaldo, declarado en el registro"


def sin_secretos(texto: str, raiz: Path = Path(".")) -> tuple[bool, str]:
    if CLAVE_GOOGLE.search(texto) or ASIGNACION.search(texto):
        return False, "el registro tiene forma de secreto"
    _, versionados = git("ls-files", ".env", raiz=raiz)
    if versionados:
        return False, ".env está en el repositorio"
    return True, "ningún valor con forma de secreto"


def ejecutar(raiz: Path = Path(".")) -> bool:
    texto = leer(raiz)
    if texto is None:
        print(f"FALLA REG-1 no existe {REGISTRO}")
        return False
    comprobaciones = [
        ("REG-1", "estructura del registro", estructura),
        ("REG-2", "secciones manuales escritas", manual_completo),
        ("REG-3", "commit vigente", lambda t: commit_vigente(t, raiz)),
        ("REG-4", "cifras coherentes con la tabla", cifras_coherentes),
        ("REG-5", "respaldos declarados", respaldos_declarados),
        ("REG-6", "sin secretos", lambda t: sin_secretos(t, raiz)),
    ]
    cumplidas = 0
    for id_, descripcion, prueba in comprobaciones:
        try:
            ok, evidencia = prueba(texto)
        except Exception as error:
            ok, evidencia = False, f"error: {error!r}"
        estado = "PASA " if ok else "FALLA"
        print(f"{estado} {id_} {descripcion} -> {evidencia}")
        cumplidas += 1 if ok else 0
    total = len(comprobaciones)
    print(f"\n{cumplidas} de {total} comprobaciones cumplidas")
    return cumplidas == total


if __name__ == "__main__":
    raise SystemExit(0 if ejecutar() else 1)
