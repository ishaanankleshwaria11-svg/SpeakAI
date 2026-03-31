from typing import Dict, List, Tuple
import re

from . import config
from .utils import highlight_fillers, tokenize


def detect_fillers(transcript: str, fillers: List[str] = None) -> Tuple[str, Dict[str, int]]:
    fillers = fillers or config.FILLER_WORDS
    words = transcript.split()
    highlighted, counts = highlight_fillers(words, fillers)
    return highlighted, counts


def filler_density(counts: Dict[str, int], duration_sec: float) -> float:
    total = sum(counts.values())
    minutes = duration_sec / 60 if duration_sec else 1
    return total / minutes if minutes else total


def most_repeated(counts: Dict[str, int]) -> str:
    if not counts:
        return "None"
    return max(counts.items(), key=lambda kv: kv[1])[0]
