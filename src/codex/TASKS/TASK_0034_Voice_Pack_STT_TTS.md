# Task 34: Voice Pack (STT/TTS)

**Goal**: Offline push‑to‑talk commands and responses.

**Scope**
- whisper.cpp service for STT; Piper for TTS
- Push‑to‑talk hotkey; VAD; device selection
- Map utterances to actions/workflows; speak responses

**Acceptance**
- STT latency <1s for short commands on CPU
- TTS plays within 500ms of text availability
- Works fully offline
