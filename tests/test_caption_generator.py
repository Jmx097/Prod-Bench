#!/usr/bin/env python3
"""Unit tests for CaptionGeneratorAgent."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCaptionGeneratorAgent:
    """Tests for CaptionGeneratorAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create agent with default config."""
        from execution.agents.caption_generator import CaptionGeneratorAgent
        return CaptionGeneratorAgent({
            "whisper_model": "tiny",
            "language": "en",
            "max_words_per_line": 10,
            "max_chars_per_line": 42,
        })
    
    def test_format_timestamp(self, agent):
        """Test SRT timestamp formatting."""
        assert agent._format_timestamp(0) == "00:00:00,000"
        assert agent._format_timestamp(61.5) == "00:01:01,500"
        assert agent._format_timestamp(3661.123) == "01:01:01,123"
    
    def test_segment_to_srt_lines_respects_word_limit(self, agent):
        """Test that segments are split by word count."""
        segment = {
            "start": 0,
            "end": 10,
            "text": "one two three four five six seven eight nine ten eleven twelve",
            "words": [
                {"word": "one", "start": 0, "end": 0.5},
                {"word": "two", "start": 0.5, "end": 1},
                {"word": "three", "start": 1, "end": 1.5},
                {"word": "four", "start": 1.5, "end": 2},
                {"word": "five", "start": 2, "end": 2.5},
                {"word": "six", "start": 2.5, "end": 3},
                {"word": "seven", "start": 3, "end": 3.5},
                {"word": "eight", "start": 3.5, "end": 4},
                {"word": "nine", "start": 4, "end": 4.5},
                {"word": "ten", "start": 4.5, "end": 5},
                {"word": "eleven", "start": 5, "end": 5.5},
                {"word": "twelve", "start": 5.5, "end": 6},
            ]
        }
        
        lines = agent._segment_to_srt_lines(segment)
        
        # With max_words_per_line=10, should split into 2 lines
        assert len(lines) >= 2
        for start, end, text in lines:
            assert len(text.split()) <= 10
    
    def test_segment_fallback_without_words(self, agent):
        """Test fallback when word timestamps not available."""
        segment = {
            "start": 0,
            "end": 5,
            "text": "Hello world"
        }
        
        lines = agent._segment_to_srt_lines(segment)
        
        assert len(lines) == 1
        assert lines[0] == (0, 5, "Hello world")
    
    def test_process_returns_correct_structure(self, agent, tmp_path):
        """Test result dict structure."""
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        
        with patch("subprocess.run") as mock_run, \
             patch.object(agent, "_transcribe") as mock_transcribe:
            
            mock_run.return_value = MagicMock(returncode=0)
            mock_transcribe.return_value = [
                {"start": 0, "end": 2, "text": "Hello world", "words": []}
            ]
            
            output_dir.mkdir(exist_ok=True)
            result = agent.process(str(input_file), str(output_dir))
        
        assert "success" in result
        assert "agent" in result
        assert result["agent"] == "CaptionGeneratorAgent"

    def test_burn_captions(self, agent, tmp_path):
        """Test burn_captions flag triggers ffmpeg call."""
        agent.config["burn_captions"] = True
        input_file = tmp_path / "input.mp4"
        input_file.touch()
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        with patch("subprocess.run") as mock_run, \
             patch.object(agent, "_transcribe", return_value=[]):
            
            mock_run.return_value = MagicMock(returncode=0)
            
            result = agent.process(str(input_file), str(output_dir))
            
            # Should have called ffmpeg for audio, then burn
            # We expect at least one call with "subtitles=" in args
            burn_call_found = False
            for call in mock_run.call_args_list:
                args = call[0][0] # cmd list
                if any("subtitles=" in arg for arg in args):
                    burn_call_found = True
                    break
            
            assert burn_call_found
            assert "burned_video_path" in result
