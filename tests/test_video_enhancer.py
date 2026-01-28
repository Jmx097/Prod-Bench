#!/usr/bin/env python3
"""Unit tests for VideoEnhancerAgent."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestVideoEnhancerAgent:
    """Tests for VideoEnhancerAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with default config."""
        from execution.agents.video_enhancer import VideoEnhancerAgent
        return VideoEnhancerAgent({
            "lut_path": None,
            "output_codec": "h264",
            "crf": 18,
            "hardware_acceleration": False,
            "software_encoder": "libx264",
        })
    
    def test_get_encoder_args_software(self, agent):
        """Test software encoder argument generation."""
        args = agent._get_encoder_args()
        
        assert "-c:v" in args
        assert "libx264" in args
        assert "-crf" in args
        assert "18" in args
    
    def test_build_video_filter_no_lut(self, agent):
        """Test that no filter is built without LUT."""
        filter_str = agent._build_video_filter(None)
        assert filter_str == ""
    
    def test_build_video_filter_with_lut(self, agent, tmp_path):
        """Test LUT filter generation."""
        lut_file = tmp_path / "test.cube"
        lut_file.touch()
        
        filter_str = agent._build_video_filter(lut_file)
        
        assert "lut3d=" in filter_str
        assert "trilinear" in filter_str
    
    def test_supported_lut_formats(self, agent):
        """Test LUT format validation."""
        assert ".cube" in agent.SUPPORTED_LUT_FORMATS
        assert ".3dl" in agent.SUPPORTED_LUT_FORMATS
        assert ".mp4" not in agent.SUPPORTED_LUT_FORMATS
    
    @patch("subprocess.run")
    def test_process_calls_ffmpeg(self, mock_run, agent, tmp_path):
        """Test that process calls FFmpeg."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        def create_output(*args, **kwargs):
            (output_dir / "input_enhanced.mp4").touch()
            return MagicMock(returncode=0, stderr="")
        
        mock_run.side_effect = create_output
        
        result = agent.process(str(input_file), str(output_dir))
        
        assert mock_run.called
        assert "ffmpeg" in mock_run.call_args[0][0]
    
    def test_hardware_fallback(self, tmp_path):
        """Test that hardware unavailable falls back to software."""
        from execution.agents.video_enhancer import VideoEnhancerAgent
        
        agent = VideoEnhancerAgent({
            "hardware_acceleration": True,
            "hardware_encoder": "nonexistent_encoder",
            "software_encoder": "libx264",
            "crf": 18,
        })
        
        with patch("subprocess.run") as mock_run:
            # Mock encoder check to fail
            mock_run.return_value = MagicMock(returncode=0, stdout="")
            
            args = agent._get_encoder_args()
            
            # Should fall back to software
            assert "libx264" in args
