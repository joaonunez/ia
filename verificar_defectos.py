"""Introduce un defecto en una copia temporal y comprueba si una prueba lo detecta (U3.4 · Bloque 39).

Uso:
    python verificar_defectos.py ARCHIVO "TEXTO_ACTUAL" "TEXTO_NUEVO" PRUEBA
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

IGNORAR = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".git", ".venv", "venv", "vectorstore")


def main(archivo: str, viejo: str, nuevo: str, prueba: str) -> int:
    origen = Path(archivo)
    if not origen.exists() or not Path(prueba).exists():
        print("ERROR no existe el archivo o la prueba indicada")
        return 2
    veces = origen.read_text(encoding="utf-8").count(viejo)
    if veces != 1:
        print(f"ERROR el texto aparece {veces} veces en {archivo};")
        print(" usa un fragmento que aparezca exactamente una vez")
        return 2
    with tempfile.TemporaryDirectory() as tmp:
        copia = Path(tmp) / "copia"
        shutil.copytree(".", copia, ignore=IGNORAR)
        destino = copia / archivo
        texto = destino.read_text(encoding="utf-8")
        destino.write_text(texto.replace(viejo, nuevo), encoding="utf-8")
        r = subprocess.run(
            [sys.executable, "-m", "pytest", prueba, "-q", "--tb=no"],
            cwd=copia,
            capture_output=True,
            text=True,
            check=False,
        )
    fallan = re.findall(r"^FAILED (\S+)", r.stdout, re.MULTILINE)
    print(f"defecto en {archivo}: {viejo!r} -> {nuevo!r}")
    if fallan:
        print(f"DETECTADO: fallan {len(fallan)} prueba(s) de {prueba}")
        for nombre in fallan:
            print(" ", nombre.split("::")[-1])
        return 0
    print(f"NO DETECTADO: todas las pruebas de {prueba} siguen pasando")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print(__doc__)
        raise SystemExit(2)
    raise SystemExit(main(*sys.argv[1:]))
