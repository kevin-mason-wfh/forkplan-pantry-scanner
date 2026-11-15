import json
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz

SYNONYMS_PATH = Path(__file__).with_name("synonyms.json")
PUNCTUATION = re.compile(r"[^\w\s]", re.UNICODE)
WHITESPACE = re.compile(r"\s+")


@lru_cache(maxsize=1)
def _synonyms() -> dict[str, str]:
    raw_synonyms = json.loads(SYNONYMS_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw_synonyms, dict):
        return {}
    return {str(key): str(value) for key, value in raw_synonyms.items()}


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    cleaned = WHITESPACE.sub(" ", PUNCTUATION.sub(" ", ascii_text)).strip()
    words = cleaned.split()
    if words and len(words[-1]) > 3 and words[-1].endswith("s") and not words[-1].endswith("ss"):
        words[-1] = words[-1][:-1]
    normalized = " ".join(words)
    return _synonyms().get(normalized, normalized)


def similarity(left: str, right: str) -> int:
    return round(fuzz.ratio(normalize(left), normalize(right)))
