import datetime as dt
from dataclasses import dataclass, asdict
from typing import Dict, List

from .utils import generate_id


@dataclass
class Attempt:
    attempt_id: str
    created_at: str
    transcript: str
    scores: Dict[str, float]
    metrics: Dict
    filler_counts: Dict[str, int]


def init_state(st):
    if "attempts" not in st:
        st.attempts: List[Attempt] = []
    if "latest_transcript" not in st:
        st.latest_transcript = ""


def store_attempt(st, transcript: str, scores: Dict[str, float], metrics: Dict, fillers: Dict[str, int]):
    attempt = Attempt(
        attempt_id=generate_id(),
        created_at=dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        transcript=transcript,
        scores=scores,
        metrics=metrics,
        filler_counts=fillers,
    )
    st.attempts.append(attempt)
    st.latest_transcript = transcript


def attempts_dataframe(attempts: List[Attempt]):
    import pandas as pd

    if not attempts:
        return pd.DataFrame()
    records = [asdict(a) for a in attempts]
    return pd.DataFrame(records)
