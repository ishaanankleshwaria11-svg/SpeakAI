"""
Configuration constants for SpeakAI.
"""

FILLER_WORDS = [
    "um",
    "uh",
    "like",
    "basically",
    "you know",
    "matlab",
    "actually",
]

# Default sample rate for audio processing
SAMPLE_RATE = 16000

# Thresholds for pause detection (in seconds)
PAUSE_MIN_DURATION = 0.35
PAUSE_DB_THRESHOLD = -35  # decibels relative to max

# UI constants
APP_TITLE = "SpeakAI – Public Speaking Coach"
APP_TAGLINE = "AI-powered mentor for speeches, debates, and MUN"

# Safe defaults for scoring weights
SCORING_WEIGHTS = {
    "clarity": 0.18,
    "pace": 0.16,
    "confidence": 0.14,
    "impact": 0.14,
    "engagement": 0.18,
    "structure": 0.10,
    "vocabulary": 0.10,
}

MODEL_SIZE = "small"  # can be changed to "medium" / "large" as needed
