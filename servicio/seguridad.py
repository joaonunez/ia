"""Mitigaciones de inyección de instrucciones y fuga de datos (U3.5 · Bloque 43).

Incluye defensa en profundidad:
1. Detección de entrada normalizada (`NFKD` + `casefold`) con 4 reglas calibradas
   para evitar falsos positivos en consultas legítimas.
2. Limpieza de salida (`limpiar_salida`) que redacta instrucciones internas y
   patrones de credenciales aunque el modelo sea vulnerable.
"""
from __future__ import annotations

import re
import unicodedata

RECHAZO = "No puedo atender esa solicitud (consulta bloqueada por seguridad)."
OCULTO = "[contenido interno omitido]"
SECRETO = "[secreto omitido]"

REGLAS_ENTRADA: list[tuple[str, re.Pattern[str]]] = [
    (
        "ignorar_instrucciones",
        re.compile(
            r"\b(?:ignora|olvida|descarta|omite|anula)\b.{0,35}"
            r"\b(?:instruccion(?:es)?|reglas?|indicacion(?:es)?|contexto|prompt)\b"
        ),
    ),
    (
        "pedir_instrucciones",
        re.compile(
            r"\b(?:revela|muestra|imprime|dime|devuelve|copia|repite)\b.{0,30}"
            r"\b(?:tu|tus|el|la|las|los)\s+"
            r"(?:prompt|instruccion(?:es)?\s+(?:internas?|del\s+sistema|ocultas?|anteriores)|"
            r"reglas?\s+internas?|system\s+prompt)\b"
        ),
    ),
    (
        "cambiar_de_rol",
        re.compile(
            r"\b(?:actua\s+como|finge\s+ser|ahora\s+eres|"
            r"modo\s+(?:desarrollador|dan|sin\s+restricciones|admin))\b"
        ),
    ),
    (
        "pedir_secretos",
        re.compile(
            r"\b(?:api[_\s-]?key|gemini[_\s-]?api[_\s-]?key|"
            r"clave\s+(?:de\s+api|secreta|del\s+proveedor)|"
            r"token\s+secreto|variables?\s+de\s+entorno|\.env)\b"
        ),
    ),
]

SECRETOS: list[re.Pattern[str]] = [
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"sk-[0-9A-Za-z_-]{16,}"),
    re.compile(r"(?i)(?:GEMINI_API_KEY|API_KEY)\s*=\s*\S+"),
]


def normalizar(texto: str) -> str:
    """Normaliza Unicode (NFKD sin marcas combinantes) y aplica casefold."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return sin_tildes.casefold()


def detectar_inyeccion(texto: str) -> str | None:
    """Devuelve el nombre de la primera regla disparada o `None` si es segura."""
    norm = normalizar(texto)
    for nombre, patron in REGLAS_ENTRADA:
        if patron.search(norm):
            return nombre
    return None


def limpiar_salida(texto: str, internos: tuple[str, ...] | list[str] = ()) -> str:
    """Redacta textos internos y patrones de secretos antes de devolver la respuesta."""
    limpio = texto
    for fragmento in internos:
        if fragmento:
            limpio = re.sub(re.escape(fragmento), OCULTO, limpio, flags=re.IGNORECASE)
    for patron in SECRETOS:
        limpio = patron.sub(SECRETO, limpio)
    return limpio
