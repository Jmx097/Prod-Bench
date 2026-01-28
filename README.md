# Prod-Bench Repository

This repository contains the production code for the Antigravity Video Production Pipeline and other experimental features.

## 🎬 Video Production Pipeline

A programmatic pipeline to automate video post-production for YouTube.

**Core Features:**

- **Audio:** Loudness normalization (LUFS -16), EQ, compression.
- **Captions:** Auto-generated SRT subtitles using OpenAI Whisper.
- **Video:** Color grading (LUTs) and hardware-accelerated encoding.
- **Thumbnails:** Smart frame extraction.
- **Backup:** Automatic pre-processing backups with retention policies.

### Quick Start

```bash
# Process a video
python execution/antigravity_pipeline.py input.mp4

# Validate environment
python execution/antigravity_pipeline.py input.mp4 --dry-run
```

### Documentation

- [Setup Guide](docs/YOUTUBE_PIPELINE_SETUP.md) - Installation and configuration.
- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Using the Python API.
- [Codebase Map](docs/REUSE_MAP.md) - Traceability of reusable patterns.

### Configuration

See `execution/production_config.json` for all pipeline settings.

## Directory Structure

```
├── execution/
│   ├── agents/               # Individual worker agents
│   ├── antigravity_pipeline.py  # Main orchestrator
│   └── production_config.json   # Pipeline config
├── docs/                     # Documentation
├── tests/                    # Unit and integration tests
└── directives/               # Project directives
```
