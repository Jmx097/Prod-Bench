# YouTube Pipeline Setup Guide

Complete setup guide for the Antigravity Video Production Pipeline.

## Prerequisites

### Required Software

| Software | Version | Purpose                |
| -------- | ------- | ---------------------- |
| Python   | 3.10+   | Runtime                |
| FFmpeg   | 4.4+    | Video/audio processing |
| pip      | 21+     | Package manager        |

### Required Python Packages

```bash
pip install openai-whisper torch jsonschema
```

Optional packages:

```bash
pip install pytest  # For running tests
```

## Installation

1. **Clone the repository** (if not already done):

   ```bash
   git clone <repo-url>
   cd Prod-Bench
   ```

2. **Verify FFmpeg installation**:

   ```bash
   ffmpeg -version
   ```

3. **Verify Python and install dependencies**:

   ```bash
   python --version  # Should be 3.10+
   pip install openai-whisper torch jsonschema
   ```

4. **Test the installation**:
   ```bash
   python execution/antigravity_pipeline.py --help
   ```

## Quick Start

### Basic Usage

Process a video with default settings:

```bash
python execution/antigravity_pipeline.py input.mp4
```

Specify output directory:

```bash
python execution/antigravity_pipeline.py input.mp4 --output-dir ./output
```

### Dry Run (Validate Only)

Check configuration and prerequisites without processing:

```bash
python execution/antigravity_pipeline.py input.mp4 --dry-run
```

### Verbose Mode

Enable detailed logging:

```bash
python execution/antigravity_pipeline.py input.mp4 --verbose
```

### Custom Configuration

Use a custom config file:

```bash
python execution/antigravity_pipeline.py input.mp4 --config my_config.json
```

## Configuration Reference

The pipeline is configured via `execution/production_config.json`.

### Audio Settings

| Key                        | Default | Description                           |
| -------------------------- | ------- | ------------------------------------- |
| `target_loudness_lufs`     | -16     | YouTube standard loudness             |
| `highpass_hz`              | 80      | Remove rumble below this frequency    |
| `lowpass_hz`               | 12000   | Remove harshness above this frequency |
| `compression_threshold_db` | -20     | Compressor threshold                  |
| `compression_ratio`        | 3       | Compression ratio (3:1)               |

### Caption Settings

| Key                  | Default | Description                                  |
| -------------------- | ------- | -------------------------------------------- |
| `whisper_model`      | "base"  | Model size: tiny, base, small, medium, large |
| `language`           | "en"    | ISO language code                            |
| `max_words_per_line` | 10      | Max words per subtitle line                  |

### Thumbnail Settings

| Key       | Default | Description                      |
| --------- | ------- | -------------------------------- |
| `count`   | 6       | Number of thumbnails to generate |
| `width`   | 1280    | Thumbnail width                  |
| `height`  | 720     | Thumbnail height                 |
| `format`  | "jpg"   | Output format: jpg, png, webp    |
| `quality` | 95      | JPEG/WebP quality (1-100)        |

### Video Settings

| Key                     | Default | Description                        |
| ----------------------- | ------- | ---------------------------------- |
| `lut_path`              | null    | Path to LUT file for color grading |
| `crf`                   | 18      | Quality (lower = better, 0-51)     |
| `hardware_acceleration` | true    | Use hardware encoder if available  |

## Output Files

After processing, you'll find:

```
output_dir/
├── input_enhanced.mp4      # Final video
├── input_captions.srt      # Subtitle file
├── input_audio_normalized.wav  # Processed audio
├── thumbnails/
│   ├── thumb_01.jpg
│   ├── thumb_02.jpg
│   └── ... (6 total)
├── logs/
│   └── processing_log_*.json
└── .backups/
    └── input_*.mp4         # Original backup
```

## Running Tests

```bash
cd Prod-Bench
python -m pytest tests/ -v
```

Run specific test:

```bash
python -m pytest tests/test_audio_processor.py -v
```

## Troubleshooting

### FFmpeg Not Found

Ensure FFmpeg is in your PATH:

```bash
# Windows
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### Whisper Model Download

First run will download the Whisper model (~140MB for base). Ensure internet connection.

### Hardware Encoding Not Available

The pipeline automatically falls back to software encoding. To force software:

```json
{
  "video": {
    "hardware_acceleration": false
  }
}
```

### Memory Issues with Large Videos

Use a smaller Whisper model:

```json
{
  "captions": {
    "whisper_model": "tiny"
  }
}
```
