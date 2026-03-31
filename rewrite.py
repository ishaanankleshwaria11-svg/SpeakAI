from typing import Dict

from .nlp_feedback import hook_options, closing_lines, rewrite_transcript


def generate_hooks(topic: str) -> Dict[str, str]:
    return hook_options(topic)


def generate_closings(topic: str) -> Dict[str, str]:
    return closing_lines(topic)


def upgrade_lines(text: str) -> str:
    return rewrite_transcript(text)
