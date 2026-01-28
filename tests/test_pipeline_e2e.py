#!/usr/bin/env python3
"""End-to-end integration test for Video Production Pipeline."""

import pytest
import json
from pathlib import Path
import sys
from unittest.mock import patch, MagicMock

# Mock whisper module before it's imported by anything
mock_whisper = MagicMock()
sys.modules["whisper"] = mock_whisper

import shutil


class TestPipelineE2E:
    """End-to-end tests for VideoPipelineOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self, tmp_path):
        """Create orchestrator with test config."""
        from execution.antigravity_pipeline import VideoPipelineOrchestrator
        
        # Create test config
        config = {
            "version": "1.0.0",
            "audio": {
                "target_loudness_lufs": -16,
                "highpass_hz": 80,
                "lowpass_hz": 12000,
                "compression_threshold_db": -20,
                "compression_ratio": 3,
            },
            "captions": {
                "whisper_model": "tiny",
                "language": "en",
                "max_words_per_line": 10,
            },
            "video": {
                "lut_path": None,
                "output_codec": "h264",
                "crf": 18,
                "hardware_acceleration": False,
                "software_encoder": "libx264",
            },
            "thumbnails": {
                "count": 6,
                "width": 1280,
                "height": 720,
                "format": "jpg",
                "quality": 95,
            },
            "backup": {
                "enabled": True,
                "backup_dir": ".backups",
                "retention_days": 7,
            },
            "logging": {
                "output_dir": "logs",
                "log_level": "INFO",
                "persist_json": True,
            },
            "pipeline": {
                "temp_dir": ".tmp",
                "cleanup_temp": True,
                "fail_fast": False,
            }
        }
        
        config_path = tmp_path / "test_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        return VideoPipelineOrchestrator(config_path=str(config_path))
    
    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly."""
        assert orchestrator is not None
        assert orchestrator.config is not None
        assert orchestrator.config["version"] == "1.0.0"
    
    def test_dry_run(self, orchestrator, tmp_path):
        """Test dry run validation."""
        # Create fake video
        video = tmp_path / "test.mp4"
        video.touch()
        
        with patch.object(orchestrator, "_check_ffmpeg", return_value=True), \
             patch.object(orchestrator, "_check_whisper", return_value=True):
            
            result = orchestrator.dry_run(str(video))
        
        assert "checks" in result
        assert "config" in result
        assert result["checks"]["video_exists"] is True
    
    def test_dry_run_missing_video(self, orchestrator, tmp_path):
        """Test dry run with missing video."""
        result = orchestrator.dry_run(str(tmp_path / "nonexistent.mp4"))
        
        assert result["checks"]["video_exists"] is False
        assert result["all_passed"] is False
    
    def test_process_returns_expected_structure(self, orchestrator, tmp_path):
        """Test that process returns all required keys."""
        video = tmp_path / "test.mp4"
        video.touch()
        output_dir = tmp_path / "output"
        
        # Mock all agent processes
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="10.0", stderr="")
            
            # Create expected output files
            def setup_outputs(*args, **kwargs):
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "test_audio_normalized.wav").touch()
                (output_dir / "test_captions.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nTest\n\n")
                (output_dir / "test_enhanced.mp4").touch()
                thumb_dir = output_dir / "thumbnails"
                thumb_dir.mkdir(exist_ok=True)
                for i in range(1, 7):
                    (thumb_dir / f"thumb_{i:02d}.jpg").touch()
                (output_dir / ".backups").mkdir(exist_ok=True)
                shutil.copy(video, output_dir / ".backups" / "test_backup.mp4")
                return MagicMock(returncode=0, stdout="10.0", stderr="")
            
            mock_run.side_effect = setup_outputs
            
            with patch("whisper.load_model") as mock_whisper:
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {
                    "segments": [{"start": 0, "end": 1, "text": "Test", "words": []}]
                }
                mock_whisper.return_value = mock_model
                
                result = orchestrator.process(str(video), output_dir=str(output_dir))
        
        # Check required keys
        assert "final_video_path" in result
        assert "captions_srt_path" in result
        assert "thumbnail_paths" in result
        assert "processing_log_path" in result
        assert "total_time" in result
        assert "error_messages" in result
        
        # Check types
        assert isinstance(result["thumbnail_paths"], list)
        assert isinstance(result["error_messages"], list)
        assert isinstance(result["total_time"], float)
    
    def test_processing_log_created(self, orchestrator, tmp_path):
        """Test that JSON processing log is created."""
        video = tmp_path / "test.mp4"
        video.touch()
        output_dir = tmp_path / "output"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="10.0", stderr="")
            
            def setup_outputs(*args, **kwargs):
                output_dir.mkdir(parents=True, exist_ok=True)
                (output_dir / "test_audio_normalized.wav").touch()
                (output_dir / "test_captions.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nTest\n\n")
                (output_dir / "test_enhanced.mp4").touch()
                thumb_dir = output_dir / "thumbnails"
                thumb_dir.mkdir(exist_ok=True)
                for i in range(1, 7):
                    (thumb_dir / f"thumb_{i:02d}.jpg").touch()
                (output_dir / ".backups").mkdir(exist_ok=True)
                shutil.copy(video, output_dir / ".backups" / "test_backup.mp4")
                return MagicMock(returncode=0, stdout="10.0", stderr="")
            
            mock_run.side_effect = setup_outputs
            
            with patch("whisper.load_model") as mock_whisper:
                mock_model = MagicMock()
                mock_model.transcribe.return_value = {
                    "segments": [{"start": 0, "end": 1, "text": "Test", "words": []}]
                }
                mock_whisper.return_value = mock_model
                
                result = orchestrator.process(str(video), output_dir=str(output_dir))
        
        log_path = Path(result["processing_log_path"])
        assert log_path.exists()
        
        with open(log_path) as f:
            log_data = json.load(f)
        
        assert "timestamp" in log_data
        assert "total_time_seconds" in log_data
        assert "agent_results" in log_data


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_invalid_config_raises_error(self, tmp_path):
        """Test that invalid config raises ValueError."""
        from execution.antigravity_pipeline import VideoPipelineOrchestrator
        
        # Create invalid config
        config = {"invalid": True}  # Missing required fields
        config_path = tmp_path / "bad_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f)
        
        # Should raise or warn depending on jsonschema availability
        try:
            import jsonschema
            with pytest.raises(ValueError):
                VideoPipelineOrchestrator(config_path=str(config_path))
        except ImportError:
            # Without jsonschema, validation is skipped
            pass
