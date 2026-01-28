#!/usr/bin/env python3
"""
Thumbnail Generator Agent - Extracts high-quality thumbnails from video.

Features:
- Even keyframe extraction across video duration
- Configurable count, dimensions, and quality
- JPEG/PNG/WebP output formats
- Scoring Stub
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List

from .base_agent import BaseAgent


class ThumbnailGeneratorAgent(BaseAgent):
    """
    Generates thumbnails at even intervals across video.
    
    Config keys:
        count: Number of thumbnails (default: 6)
        width: Thumbnail width (default: 1280)
        height: Thumbnail height (default: 720)
        format: Output format jpg/png/webp (default: jpg)
        quality: JPEG/WebP quality 1-100 (default: 95)
        strategy: Extraction strategy (default: even_keyframes)
        detect_faces: Stub for face detection
    """
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Get video duration in seconds."""
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            raise RuntimeError(f"Could not get video duration: {result.stderr}")
        
        return float(result.stdout.strip())
    
    def _calculate_timestamps(self, duration: float, count: int) -> List[float]:
        """Calculate evenly-spaced timestamps for thumbnail extraction."""
        if count <= 0:
            return []
        if count == 1:
            return [duration / 2]
        
        # Avoid very beginning and end
        margin = duration * 0.05  # 5% margin
        usable_duration = duration - (2 * margin)
        interval = usable_duration / (count - 1)
        
        timestamps = []
        for i in range(count):
            ts = margin + (i * interval)
            timestamps.append(round(ts, 2))
        
        return timestamps
    
    def _get_output_extension(self) -> str:
        """Get file extension based on format config."""
        fmt = self.config.get("format", "jpg").lower()
        return {
            "jpg": ".jpg",
            "jpeg": ".jpg",
            "png": ".png",
            "webp": ".webp"
        }.get(fmt, ".jpg")
    
    def _get_quality_args(self) -> List[str]:
        """Get FFmpeg quality arguments based on format."""
        fmt = self.config.get("format", "jpg").lower()
        quality = self.config.get("quality", 95)
        
        if fmt in ("jpg", "jpeg"):
            # JPEG uses qscale (2-31, lower is better)
            qscale = max(1, int(31 - (quality / 100 * 30)))
            return ["-qscale:v", str(qscale)]
        elif fmt == "webp":
            return ["-quality", str(quality)]
        elif fmt == "png":
            return []  # PNG is lossless
        
        return []
    
    def _extract_thumbnail(
        self, 
        video_path: Path, 
        timestamp: float, 
        output_path: Path,
        width: int,
        height: int
    ) -> bool:
        """Extract a single thumbnail at the given timestamp."""
        quality_args = self._get_quality_args()
        
        cmd = [
            "ffmpeg", "-y", "-hide_banner",
            "-ss", str(timestamp),
            "-i", str(video_path),
            "-vframes", "1",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,"
                   f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            *quality_args,
            "-loglevel", "error",
            str(output_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0 and output_path.exists()

    def _calculate_score_stub(self, image_path: Path) -> float:
        """Stub for thumbnail scoring (e.g. contrast/face count)."""
        # Real impl would read image with cv2/PIL
        # For now, return randomish deterministic score
        return 0.5 + (len(image_path.name) % 5) / 10.0
    
    def _execute(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Generate thumbnails from video with scoring.
        """
        self.validate_input(input_path)
        
        # Create thumbnails subdirectory
        thumb_dir = output_dir / "thumbnails"
        thumb_dir.mkdir(parents=True, exist_ok=True)
        
        count = self.config.get("count", 6)
        width = self.config.get("width", 1280)
        height = self.config.get("height", 720)
        ext = self._get_output_extension()
        
        # Get duration and calculate timestamps
        self.logger.info(f"Analyzing video: {input_path.name}")
        duration = self._get_video_duration(input_path)
        timestamps = self._calculate_timestamps(duration, count)
        
        self.logger.info(f"Extracting {count} thumbnails at {width}x{height}")
        
        results = []
        for i, ts in enumerate(timestamps, 1):
            out_name = f"thumb_{i:02d}{ext}"
            out_path = thumb_dir / out_name
            
            self.logger.debug(f"Extracting thumbnail {i}/{count} at {ts:.2f}s")
            
            if self._extract_thumbnail(input_path, ts, out_path, width, height):
                # Calculate Score
                score = self._calculate_score_stub(out_path)
                results.append({
                    "path": str(out_path),
                    "timestamp": round(ts, 2),
                    "score": score
                })
            else:
                self.logger.warning(f"Failed to extract thumbnail at {ts:.2f}s")
        
        if not results:
            raise RuntimeError("No thumbnails were generated")
        
        self.logger.info(f"Generated {len(results)} thumbnails")
        
        return {
            "thumbnail_paths": [r["path"] for r in results],
            "details": results,
            "count": len(results),
            "timestamps": timestamps,
            "strategy": self.config.get("strategy")
        }
