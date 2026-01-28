#!/usr/bin/env python3
"""Unit tests for AudioProcessorAgent."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestAudioProcessorAgent:
    """Tests for AudioProcessorAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with default config."""
        from execution.agents.audio_processor import AudioProcessorAgent
        return AudioProcessorAgent({
            "target_loudness_lufs": -16,
            "highpass_hz": 80,
            "lowpass_hz": 12000,
            "compression_threshold_db": -20,
            "compression_ratio": 3,
        })
    
    def test_build_filter_chain(self, agent):
        """Test FFmpeg filter chain generation."""
        chain = agent._build_filter_chain()
        
        assert "highpass=f=80" in chain
        assert "lowpass=f=12000" in chain
        assert "loudnorm=I=-16" in chain
        assert "acompressor" in chain
    
    def test_filter_chain_uses_config_values(self):
        """Test that filter chain uses custom config values."""
        from execution.agents.audio_processor import AudioProcessorAgent
        
        agent = AudioProcessorAgent({
            "target_loudness_lufs": -14,
            "highpass_hz": 100,
            "lowpass_hz": 10000,
        })
        
        chain = agent._build_filter_chain()
        assert "highpass=f=100" in chain
        assert "lowpass=f=10000" in chain
        assert "loudnorm=I=-14" in chain
    
    @patch("subprocess.run")
    def test_process_calls_ffmpeg(self, mock_run, agent, tmp_path):
        """Test that process calls FFmpeg with correct arguments."""
        # Setup
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        mock_run.return_value = MagicMock(returncode=0, stderr="")
        
        # Mock output file creation
        def create_output(*args, **kwargs):
            output_path = output_dir / "input_audio_normalized.wav"
            output_path.touch()
            return MagicMock(returncode=0, stderr="")
        
        mock_run.side_effect = create_output
        
        # Execute
        result = agent.process(str(input_file), str(output_dir))
        
        # Verify
        assert mock_run.called
        call_args = mock_run.call_args[0][0]
        assert "ffmpeg" in call_args
    
    def test_process_returns_correct_structure(self, agent, tmp_path):
        """Test result dict structure."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        
        with patch("subprocess.run") as mock_run:
            # Mock successful execution
            def create_output(*args, **kwargs):
                output_dir.mkdir(exist_ok=True)
                (output_dir / "input_audio_normalized.wav").touch()
                return MagicMock(returncode=0, stderr="")
            
            mock_run.side_effect = create_output
            result = agent.process(str(input_file), str(output_dir))
        
        assert "success" in result
        assert "agent" in result
        assert "elapsed_time" in result
        assert result["agent"] == "AudioProcessorAgent"
    
    def test_validates_input_file(self, agent, tmp_path):
        """Test that missing input file raises error."""
        result = agent.process(str(tmp_path / "nonexistent.mp4"), str(tmp_path))
        
        assert result["success"] is False
        assert "not found" in result["error"].lower()
