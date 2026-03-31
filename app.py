import os
import streamlit as st
import pandas as pd

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# Expose OPENAI_API_KEY from Streamlit secrets to environment for the transcription module
if "OPENAI_API_KEY" in st.secrets:
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

import config
import state as app_state
from transcription import transcribe_audio, load_audio_bytes
from audio_analysis import analyze_audio
from filler_detection import detect_fillers, filler_density, most_repeated
from nlp_feedback import compute_scores, coaching_insights
from rewrite import generate_hooks, generate_closings, upgrade_lines
from ui_components import hero, score_cards, radar_chart, pace_chart, filler_bar

# Optional community component for recording
try:
    from st_audiorec import st_audiorec
except Exception:  # pragma: no cover
    st_audiorec = None


st.set_page_config(
    page_title=config.APP_TITLE,
    layout="wide",
    page_icon="🎤",
)

# Custom styling
st.markdown(
    """
    <style>
    body {background: #0b1224;}
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 6px;}
    .stTabs [data-baseweb="tab"] {background: #111827; color: #e2e8f0; padding: 10px 14px; border-radius: 12px;}
    .stTabs [data-baseweb="tab"][aria-selected="true"] {background: linear-gradient(135deg,#22d3ee33,#111827);}
    .metric-label {color:#cbd5e1;}
    </style>
    """,
    unsafe_allow_html=True,
)

app_state.init_state(st.session_state)
hero()

# Sidebar: zero-setup deployment note
with st.sidebar:
    st.markdown("### Deploy in 3 steps")
    st.markdown("1. Upload repo to GitHub\n2. In Streamlit Cloud, set main file to `app.py`\n3. Add `OPENAI_API_KEY` in Secrets for best transcription (optional)")
    st.caption("No local installs needed. Share the Streamlit URL or QR code after deploy.")

st.write("")  # spacer

rec_col, upload_col, play_col = st.columns([1.4, 1.4, 1.2])
audio_bytes = None

with rec_col:
    st.subheader("Record")
    if st_audiorec:
        st.caption("Use your mic and speak for up to 2 minutes.")
        audio_bytes = st_audiorec()
    else:
        st.info("Install `streamlit-audiorec` for in-browser recording. Using upload fallback.")

with upload_col:
    st.subheader("Upload audio")
    file = st.file_uploader("MP3 / WAV", type=["mp3", "wav", "m4a"], label_visibility="collapsed")
    if file:
        audio_bytes = load_audio_bytes(file)

with play_col:
    st.subheader("Player")
    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
    else:
        st.markdown("Waiting for audio…")


def process_audio(audio_data: bytes):
    with st.spinner("Transcribing with Whisper / faster-whisper..."):
        transcript, meta = transcribe_audio(audio_data)
    highlighted, filler_counts = detect_fillers(transcript)

    with st.spinner("Analyzing pace, pauses, and energy..."):
        metrics = analyze_audio(audio_data, transcript)

    density = filler_density(filler_counts, metrics.get("duration"))
    scores = compute_scores(metrics, density)
    filler_word = most_repeated(filler_counts)
    insights = coaching_insights(transcript, scores, metrics, filler_word)

    app_state.store_attempt(st.session_state, transcript, scores, metrics, filler_counts)

    return {
        "transcript": transcript,
        "highlighted": highlighted,
        "meta": meta,
        "metrics": metrics,
        "scores": scores,
        "filler_counts": filler_counts,
        "insights": insights,
        "filler_word": filler_word,
    }


result = None
if audio_bytes:
    result = process_audio(audio_bytes)
    st.success("Analysis ready — scroll for feedback.")

tabs = st.tabs(["Transcript", "Analysis", "Upgrade My Speech", "Compare Attempts"])

with tabs[0]:
    st.subheader("Transcript with filler highlights")
    if result:
        st.markdown(
            f"<div style='padding:12px;border-radius:12px;background:#0f172a;border:1px solid #1f2937;color:#e2e8f0;height:280px;overflow-y:auto;'>{result['highlighted']}</div>",
            unsafe_allow_html=True,
        )
        meta = result.get("meta", {})
        st.caption(f"Language: {meta.get('language', 'en')} | Duration: {meta.get('duration', '—')} sec")
        if meta.get("duration") is None:
            st.info("Add OPENAI_API_KEY in Streamlit secrets to enable full Whisper transcription quality.")
    else:
        st.info("Record or upload to view transcript.")

with tabs[1]:
    left, right = st.columns([1.8, 1.2])
    with left:
        st.subheader("Scores")
        if result:
            score_cards({k: v for k, v in result["scores"].items() if k != "overall"})
            st.metric("Overall Speech Score", int(result["scores"]["overall"]))
            radar_chart({k: v for k, v in result["scores"].items() if k != "overall"})
        else:
            st.info("No scores yet.")

        st.markdown("### Coaching Tips")
        if result:
            for tip in result["insights"]:
                st.markdown(f"- {tip}")
        else:
            st.info("Tips will appear after analysis.")

    with right:
        st.subheader("Pace")
        if result:
            pace_chart(result["metrics"]["pace_trend"])
            st.markdown(f"Words per minute: **{result['metrics']['pace_wpm']:.0f}**")
        st.subheader("Fillers")
        if result:
            filler_bar(result["filler_counts"])
            st.caption(f"Density per minute: {result['filler_counts'] and round(sum(result['filler_counts'].values())/max(result['metrics']['duration']/60,1),2)}")

with tabs[2]:
    st.subheader("Upgrade My Speech")
    default_text = result["transcript"] if result else st.session_state.get("latest_transcript", "")
    text = st.text_area("Paste any paragraph to enhance", value=default_text, height=160)
    topic = st.text_input("Topic / motion", value="public speaking")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Rewrite stronger lines"):
            upgraded = upgrade_lines(text)
            st.markdown("**Upgraded version**")
            st.write(upgraded)
    with col2:
        if st.button("Generate hooks"):
            hooks = generate_hooks(topic)
            for k, v in hooks.items():
                st.markdown(f"**{k}:** {v}")

    st.markdown("### Closing Lines")
    closings = generate_closings(topic)
    cols = st.columns(2)
    for (k, v), col in zip(closings.items(), cols * 2):
        with col:
            st.markdown(f"**{k}:** {v}")

with tabs[3]:
    st.subheader("Compare attempts")
    df = app_state.attempts_dataframe(st.session_state.attempts)
    if not df.empty:
        st.dataframe(df[["created_at", "scores", "filler_counts"]], use_container_width=True)
        chart_df = pd.DataFrame(
            [
                {
                    "created_at": row["created_at"],
                    "Overall": row["scores"].get("overall"),
                    "Pace": row["scores"].get("pace"),
                    "Clarity": row["scores"].get("clarity"),
                }
                for _, row in df.iterrows()
            ]
        ).set_index("created_at")
        st.line_chart(chart_df)
    else:
        st.info("Make at least two attempts to compare progress.")
