"""
Audio feature extraction for pace, pauses, energy, and monotone risk.
"""
from typing import Dict, List, Tuple
import io
import numpy as np

from . import config
from .utils import safe_div, moving_average, wpm

try:
    import librosa
except Exception:  # pragma: no cover
    librosa = None

try:
    from pydub import AudioSegment, silence
except Exception:  # pragma: no cover
    AudioSegment = None
    silence = None


def _load_audio(audio_bytes: bytes, sample_rate: int = config.SAMPLE_RATE) -> Tuple[np.ndarray, int]:
    if librosa:
        audio_array, sr = librosa.load(io.BytesIO(audio_bytes), sr=sample_rate)
        return audio_array, sr
    if AudioSegment:
        seg = AudioSegment.from_file(io.BytesIO(audio_bytes))
        sr = seg.frame_rate
        samples = np.array(seg.get_array_of_samples()).astype(np.float32) / (2 ** 15)
        return samples, sr
    # Minimal fallback
    return np.zeros(sample_rate), sample_rate


def analyze_audio(audio_bytes: bytes, transcript: str = "") -> Dict:
    y, sr = _load_audio(audio_bytes)
    duration = safe_div(len(y), sr)

    energy = y ** 2
    rms = np.sqrt(np.mean(energy)) if len(energy) else 0
    energy_variation = float(np.std(energy)) if len(energy) else 0

    # Pace
    words = transcript.split()
    pace_wpm = wpm(len(words), duration)

    # Pause detection (simple energy-based)
    pauses = detect_pauses(y, sr)
    pause_durations = [p[1] for p in pauses]
    long_pause_count = sum(1 for d in pause_durations if d >= 1.0)
    silence_ratio = safe_div(sum(pause_durations), duration)

    # Monotone approximation via pitch variance if librosa available
    monotone_risk = 0.5
    pitch_var = None
    if librosa and len(y):
        try:
            f0, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz("C2"), fmax=librosa.note_to_hz("C7"))
            f0 = f0[~np.isnan(f0)]
            pitch_var = np.var(f0) if f0.size else 0
            monotone_risk = float(max(0, 1 - min(pitch_var / 50, 1)))
        except Exception:
            monotone_risk = 0.5

    pace_trend = build_pace_trend(len(words), duration)

    return {
        "duration": duration,
        "rms": rms,
        "energy_variation": energy_variation,
        "pace_wpm": pace_wpm,
        "long_pause_count": long_pause_count,
        "silence_ratio": silence_ratio,
        "monotone_risk": monotone_risk,
        "pitch_variance": pitch_var,
        "pace_trend": pace_trend,
        "pause_durations": pause_durations,
    }


def detect_pauses(y: np.ndarray, sr: int) -> List[Tuple[float, float]]:
    """
    Returns list of (start_sec, duration_sec) pauses.
    """
    if silence and len(y):
        seg = AudioSegment(
            y.tobytes(),
            frame_rate=sr,
            sample_width=y.dtype.itemsize,
            channels=1,
        )
        silent_ranges = silence.detect_silence(
            seg,
            min_silence_len=int(config.PAUSE_MIN_DURATION * 1000),
            silence_thresh=config.PAUSE_DB_THRESHOLD,
        )
        return [(s / 1000, (e - s) / 1000) for s, e in silent_ranges]

    # Simple RMS gate fallback
    if not len(y):
        return []
    frame_length = int(0.03 * sr)
    hop = frame_length // 2
    rms = np.sqrt(librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop)).flatten() if librosa else np.array([])
    if rms.size == 0:
        return []
    threshold = np.percentile(rms, 20)
    pauses = []
    start = None
    for i, val in enumerate(rms):
        if val < threshold and start is None:
            start = i * hop / sr
        elif val >= threshold and start is not None:
            end = i * hop / sr
            dur = end - start
            if dur >= config.PAUSE_MIN_DURATION:
                pauses.append((start, dur))
            start = None
    return pauses


def build_pace_trend(word_count: int, duration: float) -> List[float]:
    if not duration or duration <= 0:
        return []
    segments = 8
    pace = []
    words_per_segment = word_count / segments if segments else word_count
    for i in range(segments):
        pace.append(words_per_segment / (duration / segments) * 60 if duration else 0)
    return moving_average(pace, window=2)
