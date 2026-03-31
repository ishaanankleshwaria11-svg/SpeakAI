# SpeakAI – Streamlit Public Speaking Coach

Cloud-only deployment (no local setup):

1. Upload these files to a GitHub repo.
2. In Streamlit Community Cloud: “New app” → pick the repo/branch → main file `app.py` → Deploy.
3. In the Streamlit app settings, add a secret `OPENAI_API_KEY` for best Whisper transcription (optional but recommended).

That’s it—share the generated Streamlit URL or QR code.

Features
- Browser upload or mic recording (with `streamlit-audiorec`).
- Whisper API transcription (when `OPENAI_API_KEY` is set) with filler highlighting.
- Audio analytics: pace/WPM, pauses, silence ratio, energy variation, monotone risk.
- Coaching feedback, hooks, closing lines, rewrite assistant.
- Progress comparison across attempts.
