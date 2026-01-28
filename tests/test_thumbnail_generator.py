#!/usr/bin/env python3
"""Unit tests for ThumbnailGeneratorAgent."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestThumbnailGeneratorAgent:
    """Tests for ThumbnailGeneratorAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with default config."""
        from execution.agents.thumbnail_generator import ThumbnailGeneratorAgent
        return ThumbnailGeneratorAgent({
            "count": 6,
            "width": 1280,
            "height": 720,
            "format": "jpg",
            "quality": 95,
        })
    
    def test_calculate_timestamps_even_distribution(self, agent):
        """Test that timestamps are evenly distributed."""
        timestamps = agent._calculate_timestamps(duration=100, count=6)
        
        assert len(timestamps) == 6
        # Should be roughly evenly spaced
        assert timestamps[0] > 0  # Not at very beginning
        assert timestamps[-1] < 100  # Not at very end
    
    def test_calculate_timestamps_single(self, agent):
        """Test single thumbnail is at middle."""
        timestamps = agent._calculate_timestamps(duration=100, count=1)
        
        assert len(timestamps) == 1
        assert timestamps[0] == 50  # Middle of video
    
    def test_calculate_timestamps_zero_count(self, agent):
        """Test zero count returns empty list."""
        timestamps = agent._calculate_timestamps(duration=100, count=0)
        assert timestamps == []
    
    def test_get_output_extension(self, agent):
        """Test file extension mapping."""
        assert agent._get_output_extension() == ".jpg"
        
        from execution.agents.thumbnail_generator import ThumbnailGeneratorAgent
        png_agent = ThumbnailGeneratorAgent({"format": "png"})
        assert png_agent._get_output_extension() == ".png"
    
    def test_process_creates_thumbnails_dir(self, agent, tmp_path):
        """Test that thumbnails subdirectory is created."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="60.0")
            
            # Mock thumbnail creation
            def create_thumb(*args, **kwargs):
                thumb_dir = output_dir / "thumbnails"
                thumb_dir.mkdir(parents=True, exist_ok=True)
                for i in range(1, 7):
                    (thumb_dir / f"thumb_{i:02d}.jpg").touch()
                return MagicMock(returncode=0, stdout="60.0")
            
            mock_run.side_effect = create_thumb
            
            result = agent.process(str(input_file), str(output_dir))
        
        assert (output_dir / "thumbnails").exists()
        
        # Verify score creation
        assert "details" in result
        assert len(result["details"]) > 0
        assert "score" in result["details"][0]
        assert isinstance(result["details"][0]["score"], float)
