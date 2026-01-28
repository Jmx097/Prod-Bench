#!/usr/bin/env python3
"""
Audio Processor Agent - Normalizes and enhances audio for YouTube.

Features:
- Loudness normalization to LUFS target (YouTube standard: -16)
- High-pass filter to remove rumble
- Low-pass filter to remove harsh highs
- Presence boost for voice clarity
- Gentle compression for consistent levels
"""

import subprocess
from pathlib import Path
from typing import Dict, Any

from .base_agent import BaseAgent


class AudioProcessorAgent(BaseAgent):
    """
    Processes audio: EQ, compression, and loudness normalization.
    
    Config keys:
        target_loudness_lufs: Target loudness (default: -16)
        highpass_hz: Highpass cutoff (default: 80)
        lowpass_hz: Lowpass cutoff (default: 12000)
        compression_threshold_db: Compressor threshold (default: -20)
        compression_ratio: Compression ratio (default: 3)
        presence_boost_hz: Presence EQ center (default: 3000)
        presence_boost_db: Presence boost amount (default: 2)
    """
    
    def _build_filter_chain(self) -> str:
        """Build FFmpeg audio filter chain from config."""
        cfg = self.config
        
        filters = [
            # Highpass - remove rumble
            f"highpass=f={cfg.get('highpass_hz', 80)}",
            # Lowpass - remove harsh highs
            f"lowpass=f={cfg.get('lowpass_hz', 12000)}",
            # Presence boost for clarity
            f"equalizer=f={cfg.get('presence_boost_hz', 3000)}:t=q:w=1.5:g={cfg.get('presence_boost_db', 2)}",
            # Gentle compression
            f"acompressor=threshold={cfg.get('compression_threshold_db', -20)}dB:"
            f"ratio={cfg.get('compression_ratio', 3)}:attack=5:release=50",
            # Loudness normalization (YouTube standard)
            f"loudnorm=I={cfg.get('target_loudness_lufs', -16)}:TP=-1.5:LRA=11",
        ]
        
        return ",".join(filters)
    
    def _get_loudness_stats(self, audio_path: Path) -> Dict[str, float]:
        """Analyze audio loudness using FFmpeg."""
        cmd = [
            "ffmpeg", "-hide_banner", "-i", str(audio_path),
            "-af", "loudnorm=print_format=json",
            "-f", "null", "-"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            # Parse loudnorm JSON from stderr
            import json
            import re
            
            # Find JSON block in output
            json_match = re.search(r'\{[^{}]+\}', result.stderr, re.DOTALL)
            if json_match:
                stats = json.loads(json_match.group())
                return {
                    "input_i": float(stats.get("input_i", 0)),
                    "input_tp": float(stats.get("input_tp", 0)),
                    "input_lra": float(stats.get("input_lra", 0)),
                }
        except Exception as e:
            self.logger.warning(f"Could not get loudness stats: {e}")
        
        return {}
    
    def _execute(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Process audio from video file.
        
        Returns:
            {
                "output_path": str - Path to processed audio file,
                "loudness_stats": dict - Pre/post processing stats
            }
        """
        self.validate_input(input_path)
        
        output_path = output_dir / f"{input_path.stem}_audio_normalized.wav"
        filter_chain = self._build_filter_chain()
        
        self.logger.info(f"Extracting and processing audio from {input_path.name}")
        self.logger.debug(f"Filter chain: {filter_chain}")
        
        # Get pre-processing stats
        pre_stats = self._get_loudness_stats(input_path)
        
        # Process audio
        cmd = [
            "ffmpeg", "-y", "-hide_banner",
            "-i", str(input_path),
            "-vn",  # No video
            "-af", filter_chain,
            "-ar", "48000",  # 48kHz sample rate
            "-ac", "2",  # Stereo
            "-c:a", "pcm_s16le",  # WAV format
            "-loglevel", "error",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg audio processing failed: {result.stderr}")
        
        if not output_path.exists():
            raise RuntimeError("Audio output file was not created")
        
        # Get post-processing stats
        post_stats = self._get_loudness_stats(output_path)
        
        self.logger.info(f"Audio processed successfully: {output_path.name}")
        
        return {
            "output_path": str(output_path),
            "loudness_stats": {
                "pre": pre_stats,
                "post": post_stats,
                "target_lufs": self.config.get("target_loudness_lufs", -16)
            }
        }
