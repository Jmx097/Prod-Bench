#!/usr/bin/env python3
"""
Antigravity Video Production Pipeline - Agent Exports

All agents follow a common interface:
    agent = Agent(config)
    result = agent.process(input_path, output_dir)
"""

from .base_agent import BaseAgent
from .audio_processor import AudioProcessorAgent
from .caption_generator import CaptionGeneratorAgent
from .video_enhancer import VideoEnhancerAgent
from .thumbnail_generator import ThumbnailGeneratorAgent
from .backup_manager import BackupManagerAgent

__all__ = [
    "BaseAgent",
    "AudioProcessorAgent",
    "CaptionGeneratorAgent",
    "VideoEnhancerAgent",
    "ThumbnailGeneratorAgent",
    "BackupManagerAgent",
]
