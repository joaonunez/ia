"""Limpieza y tokenización del texto antes de medirlo.

Sin este paso, una mayúscula o un punto cuentan como otra palabra.
No quita stopwords ni lematiza: eso puede esconder una diferencia real.
"""
import re
from collections import Counter


def clean_text(text: str) -> str:
    """Minúsculas, sin puntuación y con un solo espacio entre palabras."""
    if not isinstance(text, str):
        kind = type(text).__name__
        raise TypeError(f"clean_text espera str, no {kind}")
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(clean: str) -> list[str]:
    """Parte el texto ya limpio por espacios."""
    return clean.split()


def vectorize(tokens: list[str]) -> Counter:
    """Cuenta cuántas veces aparece cada token. Es una bolsa de palabras."""
    return Counter(tokens)


def process_text(text: str) -> list[str]:
    """Limpia y tokeniza. Hay que usarla en los dos lados de la comparación."""
    return tokenize(clean_text(text))
