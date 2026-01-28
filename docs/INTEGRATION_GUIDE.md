# Video Pipeline Integration Guide

Guide for integrating the Antigravity Video Production Pipeline into your applications.

## Programmatic Usage

### Basic Integration

```python
from execution.antigravity_pipeline import VideoPipelineOrchestrator

# Initialize with default config
orchestrator = VideoPipelineOrchestrator()

# Process a video
result = orchestrator.process("input.mp4")

# Access outputs
print(f"Video: {result['final_video_path']}")
print(f"Captions: {result['captions_srt_path']}")
print(f"Thumbnails: {result['thumbnail_paths']}")
print(f"Time: {result['total_time']}s")
```

### Custom Configuration

```python
# Use custom config file
orchestrator = VideoPipelineOrchestrator(config_path="custom_config.json")

# Or override at runtime
result = orchestrator.process(
    "input.mp4",
    config_overrides={
        "thumbnails": {"count": 10},
        "captions": {"whisper_model": "medium"}
    }
)
```

### Error Handling

````python
result = orchestrator.process("input.mp4")

if result["error_messages"]:
    print("Errors occurred:")
    for error in result["error_messages"]:
        print(f"  - {error}")
else:
    print("Success!")
### Enhanced Features (Phase 2/3)

The pipeline now supports:
- **Audio Muxing**: Automatically merges processed audio into the enhanced video.
- **Caption Burning**: Hard-subtitles can be burned into the output video.
- **Cloud Backup**: Stub for uploading backups to Google Drive.
- **Thumbnail Scoring**: Frame extracts include a basic score metric.

To utilize these programmatically:

```python
# Enable caption burning
orchestrator.config["captions"]["burn_captions"] = True

# Enable cloud backup logic
orchestrator.config["backup"]["upload_to_drive"] = True

result = orchestrator.process("input.mp4", "output/")
````

### Dry Run Validation

```python
validation = orchestrator.dry_run("input.mp4")

if validation["all_passed"]:
    result = orchestrator.process("input.mp4")
else:
    print("Validation failed:", validation["checks"])
```

## Return Value Structure

```python
{
    "final_video_path": str,        # Path to enhanced video
    "captions_srt_path": str,       # Path to SRT file
    "thumbnail_paths": list[str],   # List of thumbnail paths
    "processing_log_path": str,     # Path to JSON log
    "total_time": float,            # Processing time in seconds
    "error_messages": list[str]     # Empty if successful
}
```

## Using Individual Agents

Each agent can be used independently:

```python
from execution.agents import AudioProcessorAgent, ThumbnailGeneratorAgent

# Audio processing only
audio = AudioProcessorAgent({
    "target_loudness_lufs": -16,
    "highpass_hz": 80
})
result = audio.process("input.mp4", "./output")

# Thumbnail generation only
thumbs = ThumbnailGeneratorAgent({
    "count": 10,
    "width": 1920,
    "height": 1080
})
result = thumbs.process("input.mp4", "./output")
```

## Agent Interface

All agents follow a common interface:

```python
class BaseAgent:
    def __init__(self, config: dict, logger: Logger = None): ...
    def process(self, input_path: str, output_dir: str) -> dict: ...
```

Return structure:

```python
{
    "success": bool,
    "agent": str,           # Agent name
    "elapsed_time": float,  # Seconds
    "error": str | None,    # Error message if failed
    # ... agent-specific results
}
```

## CI/CD Integration

### Environment Variables

Set `CI=true` to enable safe defaults:

- Disables hardware acceleration
- Uses `tiny` Whisper model
- Extends backup retention

### GitHub Actions Example

```yaml
- name: Process Video
  env:
    CI: true
  run: |
    python execution/antigravity_pipeline.py video.mp4 --output-dir ./output

- name: Upload Artifacts
  uses: actions/upload-artifact@v3
  with:
    name: processed-video
    path: ./output/
```

### Docker Integration

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y ffmpeg
RUN pip install openai-whisper torch jsonschema

COPY execution/ /app/execution/
WORKDIR /app

ENTRYPOINT ["python", "execution/antigravity_pipeline.py"]
```

## Extending with Custom Agents

Create a new agent by extending `BaseAgent`:

```python
from execution.agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def _execute(self, input_path, output_dir):
        # Your processing logic
        return {
            "custom_output": "value"
        }
```

Register in the orchestrator:

```python
class ExtendedOrchestrator(VideoPipelineOrchestrator):
    def _create_agents(self, config):
        agents = super()._create_agents(config)
        agents["custom"] = CustomAgent(config.get("custom", {}))
        return agents
```

## Processing Log Schema

```json
{
  "timestamp": "2024-01-15T10:30:00",
  "config_path": "production_config.json",
  "total_time_seconds": 45.2,
  "success": true,
  "agent_results": {
    "backup": { "success": true, "elapsed_time": 0.5 },
    "audio": { "success": true, "elapsed_time": 8.2 },
    "captions": { "success": true, "elapsed_time": 25.1 },
    "video": { "success": true, "elapsed_time": 10.5 },
    "thumbnails": { "success": true, "elapsed_time": 0.9 }
  }
}
```

## Performance Tips

1. **Use hardware encoding** when available (default)
2. **Use smaller Whisper models** for faster processing
3. **Disable backup** for temporary files
4. **Process in parallel** if handling multiple videos

```python
from concurrent.futures import ProcessPoolExecutor

def process_video(path):
    orch = VideoPipelineOrchestrator()
    return orch.process(path)

with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(process_video, video_paths))
```
