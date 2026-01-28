# Reuse Map — Prod-Bench Patterns

Canonical patterns extracted from existing Prod-Bench codebase for reuse in Video Production Pipeline.

## Pattern Sources

| Pattern               | Source File                      | Lines   | Target Agent            |
| --------------------- | -------------------------------- | ------- | ----------------------- |
| Audio filter chain    | `jump_cut_vad.py`                | 46-53   | AudioProcessorAgent     |
| HW encoder detection  | `jump_cut_vad.py`                | 67-76   | VideoEnhancerAgent      |
| Encoder args builder  | `jump_cut_vad.py`                | 79-93   | VideoEnhancerAgent      |
| Whisper transcription | `jump_cut_vad.py`                | 121-142 | CaptionGeneratorAgent   |
| Video concat/segments | `jump_cut_vad.py`                | 363-408 | VideoEnhancerAgent      |
| LUT filter chain      | `jump_cut_vad.py`                | 352-360 | VideoEnhancerAgent      |
| Duration detection    | `jump_cut_vad.py`                | 474-481 | ThumbnailGeneratorAgent |
| Subprocess patterns   | `scrape_cross_niche_outliers.py` | 363-378 | All Agents              |
| Config from env       | `scrape_cross_niche_outliers.py` | 28-29   | Orchestrator            |

---

## Audio Filter Chain

**Source:** `jump_cut_vad.py:46-53`

```python
AUDIO_FILTERS = {
    "highpass": "highpass=f=80",
    "lowpass": "lowpass=f=12000",
    "presence": "equalizer=f=3000:t=q:w=1.5:g=2",
    "warmth": "equalizer=f=200:t=q:w=1:g=-1",
    "compression": "acompressor=threshold=-20dB:ratio=3:attack=5:release=50",
    "loudnorm": "loudnorm=I=-16:TP=-1.5:LRA=11",
}
```

**Adaptation:** Move to `production_config.json` as configurable parameters.

---

## Hardware Encoder Detection

**Source:** `jump_cut_vad.py:67-76`

```python
def check_hardware_encoder_available() -> bool:
    try:
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-encoders"],
            capture_output=True, text=True, timeout=5
        )
        return "h264_videotoolbox" in result.stdout
    except Exception:
        return False
```

**Adaptation:** Parameterize encoder name from config.

---

## Whisper Integration

**Source:** `jump_cut_vad.py:121-142`

```python
def transcribe_with_whisper(audio_path: str, model_name: str = "base"):
    model = whisper.load_model(model_name)
    result = model.transcribe(audio_path, word_timestamps=True)
    words = []
    for segment in result.get("segments", []):
        for word_info in segment.get("words", []):
            words.append({...})
    return words
```

**Adaptation:** Add SRT formatting layer.

---

## Video Duration Detection

**Source:** `jump_cut_vad.py:474-481`

```python
def get_duration(input_path: str) -> float:
    cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(result.stdout.strip())
```

**Adaptation:** Reuse directly in ThumbnailGeneratorAgent.

---

## Non-Reusable Patterns

| Pattern              | Reason                            |
| -------------------- | --------------------------------- |
| Silero VAD           | Not needed for caption generation |
| Phrase detection     | Specific to jump-cut use case     |
| Cross-niche scraping | Unrelated domain                  |
