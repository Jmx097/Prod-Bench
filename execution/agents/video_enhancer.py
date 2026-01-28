#!/usr/bin/env python3
"""
Video Enhancer Agent - Applies color grading and re-encodes video.

Features:
- LUT-based color grading
- Brightness/Contrast/Saturation adjustments
- Hardware-accelerated encoding (with software fallback)
- Quality-based encoding (CRF) or bitrate-based
- Upscaling (Stub)
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

from .base_agent import BaseAgent


class VideoEnhancerAgent(BaseAgent):
    """
    Enhances video with color grading and optimized encoding.
    
    Config keys:
        lut_path: Path to LUT file (optional)
        output_codec: Codec name (h264, h265, prores)
        crf: Constant Rate Factor for quality
        hardware_acceleration: Enable hardware encoding
        hardware_encoder: Hardware encoder name (e.g., h264_videotoolbox)
        software_encoder: Software encoder name (e.g., libx264)
        hardware_bitrate: Bitrate for hardware encoding
        brightness: Brightness adjustment (default 0.0)
        contrast: Contrast adjustment (default 1.0)
        saturation: Saturation adjustment (default 1.0)
        upscale: Enable upscaling (stub)
        denoise: Enable denoising (stub)
    """
    
    SUPPORTED_LUT_FORMATS = [".cube", ".3dl", ".dat", ".m3d", ".csp"]
    
    def _check_hardware_encoder(self) -> bool:
        """Check if hardware encoder is available."""
        hw_encoder = self.config.get("hardware_encoder", "h264_videotoolbox")
        
        try:
            result = subprocess.run(
                ["ffmpeg", "-hide_banner", "-encoders"],
                capture_output=True, text=True, timeout=5
            )
            return hw_encoder in result.stdout
        except Exception:
            return False
    
    def _get_encoder_args(self) -> List[str]:
        """Get FFmpeg encoder arguments based on config and availability."""
        use_hw = self.config.get("hardware_acceleration", True)
        
        if use_hw and self._check_hardware_encoder():
            hw_encoder = self.config.get("hardware_encoder", "h264_videotoolbox")
            bitrate = self.config.get("hardware_bitrate", "10M")
            self.logger.info(f"Using hardware encoder: {hw_encoder}")
            return ["-c:v", hw_encoder, "-b:v", bitrate]
        else:
            sw_encoder = self.config.get("software_encoder", "libx264")
            crf = self.config.get("crf", 18)
            self.logger.info(f"Using software encoder: {sw_encoder}")
            return ["-c:v", sw_encoder, "-preset", "fast", "-crf", str(crf)]
    
    def _build_video_filter(self, lut_path: Optional[Path]) -> str:
        """Construct video filter chain (LUT + EQ + Stubbed Upscale)."""
        filters = []
        
        # 1. LUT
        if lut_path and lut_path.exists():
            # Escape path for FFmpeg
            path_str = str(lut_path).replace("\\", "/").replace(":", "\\:")
            filters.append(f"lut3d='{path_str}':interp=trilinear")
            
        # 2. Basic EQ (Brightness/Contrast/Saturation)
        # eq=contrast=1.0:brightness=0.0:saturation=1.0
        cfg = self.config
        if cfg.get("brightness", 0.0) != 0.0 or cfg.get("contrast", 1.0) != 1.0 or cfg.get("saturation", 1.0) != 1.0:
            filters.append(f"eq=contrast={cfg.get('contrast', 1.0)}:brightness={cfg.get('brightness', 0.0)}:saturation={cfg.get('saturation', 1.0)}")

        # 3. Upscale Stub
        if cfg.get("upscale"):
            self.logger.warning("Upscaling requested but not implemented (Stub).")
            # filters.append("scale=3840:2160") # Example placeholder
            
        # 4. Denoise Stub
        if cfg.get("denoise"):
             filters.append("hqdn3d=1.5:1.5:6:6") # Simple light denoise
            
        return ",".join(filters) if filters else ""
    
    def _execute(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Enhance video with color grading and encoding.
        Optionally replace audio if 'external_audio_path' is in config.
        """
        self.validate_input(input_path)
        
        output_path = output_dir / f"{input_path.stem}_enhanced.mp4"
        
        # Check for LUT
        lut_path_str = self.config.get("lut_path")
        lut_path = Path(lut_path_str) if lut_path_str else None
        lut_applied = False
        
        if lut_path:
            if not lut_path.exists():
                self.logger.warning(f"LUT file not found: {lut_path}")
                lut_path = None
            elif lut_path.suffix.lower() not in self.SUPPORTED_LUT_FORMATS:
                self.logger.warning(f"Unsupported LUT format: {lut_path.suffix}")
                lut_path = None
            else:
                lut_applied = True
                self.logger.info(f"Applying LUT: {lut_path.name}")
        
        # Build command
        video_filter = self._build_video_filter(lut_path)
        encoder_args = self._get_encoder_args()
        
        cmd = [
            "ffmpeg", "-y", "-hide_banner",
            "-i", str(input_path),
        ]
        
        # Audio Muxing Logic
        external_audio = self.config.get("external_audio_path")
        if external_audio and Path(external_audio).exists():
            cmd.extend(["-i", external_audio])
            cmd.extend(["-map", "0:v:0", "-map", "1:a:0"]) # Map video from input 0, audio from input 1
            self.logger.info(f"Muxing external audio: {external_audio}")
        else:
            cmd.extend(["-map", "0:v", "-map", "0:a?"]) # Default mapping

        if video_filter:
            cmd.extend(["-vf", video_filter])
        
        cmd.extend(encoder_args)
        cmd.extend([
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",  # Web optimization
            "-loglevel", "error",
            str(output_path)
        ])
        
        self.logger.info(f"Encoding video: {input_path.name}")
        
        start = time.time()
        subprocess.run(cmd, check=True, capture_output=True, timeout=1800)  # 30 min timeout
        encoding_time = time.time() - start
        
        if not output_path.exists():
            raise RuntimeError("Enhanced video file was not created")
        
        # Determine which encoder was actually used
        encoder_used = (
            self.config.get("hardware_encoder", "h264_videotoolbox")
            if self.config.get("hardware_acceleration", True) and self._check_hardware_encoder()
            else self.config.get("software_encoder", "libx264")
        )
        
        self.logger.info(f"Video enhanced successfully in {encoding_time:.1f}s")
        
        return {
            "output_path": str(output_path),
            "encoding_time": encoding_time,
            "encoder_used": encoder_used,
            "lut_applied": lut_applied
        }
