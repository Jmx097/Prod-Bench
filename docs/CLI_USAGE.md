# CLI Usage Guide

The Video Production Pipeline includes a robust Command Line Interface (CLI) for executing the pipeline, validating configuration, and debugging.

## Basic Usage

Run the pipeline on a single video file:

```bash
python execution/antigravity_pipeline.py path/to/video.mp4
```

## Options

| Flag           | Description                                             |
| -------------- | ------------------------------------------------------- |
| `--output-dir` | Directory to save processed files (default: `./output`) |
| `--config`     | Path to `production_config.json` override               |
| `--verbose`    | Enable debug logging                                    |
| `--dry-run`    | Validate environment and config without processing      |

## Examples

### 1. Dry Run Checks

Validate that FFmpeg, Whisper, and your config are ready:

```bash
python execution/antigravity_pipeline.py dummy.mp4 --dry-run
```

### 2. Custom Configuration

Use a specific configuration file for a niche:

```bash
python execution/antigravity_pipeline.py video.mp4 --config configs/gaming_config.json
```

### 3. Debug Mode

Run with verbose logging to see FFmpeg commands:

```bash
python execution/antigravity_pipeline.py video.mp4 --verbose
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'whisper'"

Install the missing dependency:

```bash
pip install openai-whisper
```

### "FFmpeg not found"

Ensure FFmpeg is installed and added to your system `PATH`.

- **Windows**: `choco install ffmpeg`
- **Mac**: `brew install ffmpeg`

### "SRT file was not created"

Check if the audio channel extraction worked (look for `temp_audio_for_whisper.wav` in output). The model might have failed to transcribe silence.
