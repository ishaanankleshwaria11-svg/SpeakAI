"""
Rule-based NLP feedback generator that can run offline while remaining
LLM-ready when OPENAI_API_KEY is present.
"""
import os
from typing import Dict, List

from . import config
from .utils import extract_sentences, score_to_badge, soft_cap

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


def _llm_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if OpenAI and api_key:
        return OpenAI(api_key=api_key)
    return None


def compute_scores(metrics: Dict, filler_density: float, filler_bursts: int = 0) -> Dict[str, float]:
    pace_score = 100 - abs(metrics.get("pace_wpm", 0) - 140) * 0.4  # ideal ~140 wpm
    pace_score = soft_cap(pace_score, 30, 100)

    clarity = 90 - filler_density * 3
    clarity = soft_cap(clarity, 25, 100)

    confidence = 80 - metrics.get("monotone_risk", 0) * 30 - filler_bursts * 2
    confidence = soft_cap(confidence, 20, 100)

    impact = 70 + metrics.get("energy_variation", 0) * 20
    impact = soft_cap(impact, 35, 100)

    engagement = 75 - metrics.get("silence_ratio", 0) * 40
    engagement = soft_cap(engagement, 30, 100)

    structure = 70
    vocabulary = 72

    overall = (
        clarity * config.SCORING_WEIGHTS["clarity"]
        + pace_score * config.SCORING_WEIGHTS["pace"]
        + confidence * config.SCORING_WEIGHTS["confidence"]
        + impact * config.SCORING_WEIGHTS["impact"]
        + engagement * config.SCORING_WEIGHTS["engagement"]
        + structure * config.SCORING_WEIGHTS["structure"]
        + vocabulary * config.SCORING_WEIGHTS["vocabulary"]
    )

    return {
        "clarity": clarity,
        "pace": pace_score,
        "confidence": confidence,
        "impact": impact,
        "engagement": engagement,
        "structure": structure,
        "vocabulary": vocabulary,
        "overall": soft_cap(overall, 0, 100),
    }


def coaching_insights(transcript: str, scores: Dict[str, float], metrics: Dict, filler_word: str) -> List[str]:
    suggestions = []
    if scores["pace"] < 65:
        suggestions.append("Slow down slightly before key arguments; let statistics breathe.")
    if scores["clarity"] < 70 or filler_word:
        suggestions.append(f"Cut fillers like '{filler_word}' and replace with a confident pause.")
    if metrics.get("monotone_risk", 0.5) > 0.6:
        suggestions.append("Add pitch variation; mark 3 sentences to emphasize with upward tone.")
    if metrics.get("silence_ratio", 0) > 0.3:
        suggestions.append("Pauses are long; trim them to under 2 seconds except before conclusions.")
    suggestions.append("Highlight 1 statistic and 1 vivid example to boost persuasion.")
    suggestions.append("End with a crisp call-to-action that names the audience directly.")
    return suggestions


def hook_options(topic: str) -> Dict[str, str]:
    return {
        "Question": f"What if our everyday choices could rewrite the future of {topic}?",
        "Shocking Stat": f"Every minute, the world loses enough to change {topic} forever—are we ready?",
        "Story": f"When I was 12, a single moment changed how I see {topic}. Let me take you there.",
    }


def closing_lines(topic: str) -> Dict[str, str]:
    return {
        "Inspirational": f"Together, we can turn the page and make {topic} a story of hope.",
        "Debate": f"The motion is clear: {topic} demands decisive action, and the time is now.",
        "Call to Action": f"Your voice matters—take one step today to move {topic} forward.",
        "MUN Diplomatic": f"This committee has the mandate to safeguard {topic}; let us act with resolve.",
    }


def rewrite_transcript(text: str, client=None) -> str:
    client = client or _llm_client()
    if client:
        try:
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=f"Rewrite these lines to sound impactful, concise public speaking: {text}",
            )
            return response.output_text
        except Exception:
            pass
    # Fallback heuristic
    sentences = extract_sentences(text)
    upgraded = []
    for s in sentences:
        upgraded.append(_punch_up_sentence(s))
    return " ".join(upgraded)


def _punch_up_sentence(sentence: str) -> str:
    if not sentence:
        return ""
    if len(sentence.split()) < 6:
        return f"Let me be clear: {sentence}"
    return sentence.replace("I think", "I’m convinced").replace("maybe", "definitely")
