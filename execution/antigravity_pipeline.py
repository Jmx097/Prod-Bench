#!/usr/bin/env python3
"""
Antigravity Video Production Pipeline

Main orchestrator for video processing. Coordinates five agents to produce
YouTube-ready output: normalized audio, captions, thumbnails, enhancements.

Usage:
    # Basic processing
    python antigravity_pipeline.py input.mp4 --output-dir ./output

    # Dry run (validate config, skip processing)
    python antigravity_pipeline.py input.mp4 --dry-run

    # Verbose mode
    python antigravity_pipeline.py input.mp4 --verbose

    # Custom config
    python antigravity_pipeline.py input.mp4 --config custom_config.json

Programmatic usage:
    from antigravity_pipeline import VideoPipelineOrchestrator
    
    orchestrator = VideoPipelineOrchestrator()
    result = orchestrator.process("input.mp4")
"""

import os
import sys
import json
import time
import logging
import argparse
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents import (
    AudioProcessorAgent,
    CaptionGeneratorAgent,
    VideoEnhancerAgent,
    ThumbnailGeneratorAgent,
    BackupManagerAgent,
)


class VideoPipelineOrchestrator:
    """
    Main orchestrator for video production pipeline.
    
    Coordinates five agents in sequence:
    1. BackupManagerAgent - Create pre-processing backup
    2. AudioProcessorAgent - Normalize and enhance audio
    3. CaptionGeneratorAgent - Generate SRT captions
    4. VideoEnhancerAgent - Apply LUT and re-encode
    5. ThumbnailGeneratorAgent - Extract thumbnails
    
    Returns a result dict with all output paths and timing.
    """
    
    DEFAULT_CONFIG_PATH = Path(__file__).parent / "production_config.json"
    SCHEMA_PATH = Path(__file__).parent / "config_schema.json"
    
    def __init__(self, config_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize orchestrator with configuration.
        
        Args:
            config_path: Path to config JSON (uses default if not provided)
            logger: Optional logger instance
        """
        self.config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self.logger = logger or self._setup_logger()
        self.config = self._load_config()
        self._validate_config()
        
        self.logger.info(f"Loaded config from {self.config_path}")
    
    def _setup_logger(self) -> logging.Logger:
        """Create logger with console handler."""
        logger = logging.getLogger("VideoPipeline")
        logger.setLevel(logging.DEBUG)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(message)s",
                datefmt="%H:%M:%S"
            ))
            logger.addHandler(handler)
        
        return logger
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _validate_config(self) -> bool:
        """Validate config against JSON schema."""
        try:
            import jsonschema
            
            if self.SCHEMA_PATH.exists():
                with open(self.SCHEMA_PATH, "r", encoding="utf-8") as f:
                    schema = json.load(f)
                jsonschema.validate(self.config, schema)
                self.logger.debug("Config validated against schema")
            else:
                self.logger.warning(f"Schema not found: {self.SCHEMA_PATH}")
            
            return True
            
        except ImportError:
            self.logger.warning("jsonschema not installed, skipping validation")
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Config validation failed: {e.message}")
    
    def _apply_overrides(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge config overrides into base config."""
        config = json.loads(json.dumps(self.config))  # Deep copy
        
        def merge(base: Dict, updates: Dict) -> Dict:
            for key, value in updates.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge(base[key], value)
                else:
                    base[key] = value
            return base
        
        return merge(config, overrides)
    
    def _apply_ci_safety(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply CI-safe defaults when running in CI environment."""
        if os.getenv("CI", "false").lower() == "true":
            self.logger.info("CI environment detected, applying safe defaults")
            config["video"]["hardware_acceleration"] = False
            config["captions"]["whisper_model"] = "tiny"
            config["backup"]["retention_days"] = 999
        return config
    
    def _create_agents(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Instantiate all agents with config sections."""
        return {
            "backup": BackupManagerAgent(config.get("backup", {}), self.logger),
            "audio": AudioProcessorAgent(config.get("audio", {}), self.logger),
            "captions": CaptionGeneratorAgent(config.get("captions", {}), self.logger),
            "video": VideoEnhancerAgent(config.get("video", {}), self.logger),
            "thumbnails": ThumbnailGeneratorAgent(config.get("thumbnails", {}), self.logger),
        }
    
    def _save_processing_log(
        self, 
        output_dir: Path, 
        results: Dict[str, Any],
        total_time: float
    ) -> str:
        """Save JSON processing log."""
        log_dir = output_dir / self.config.get("logging", {}).get("output_dir", "logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = log_dir / f"processing_log_{timestamp}.json"
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "config_path": str(self.config_path),
            "total_time_seconds": round(total_time, 2),
            "agent_results": results,
            "success": all(r.get("success", False) for r in results.values())
        }
        
        with open(log_path, "w", encoding="utf-8") as f:
            json.dump(log_data, f, indent=2, default=str)
        
        return str(log_path)
    
    def process(
        self, 
        video_path: str, 
        output_dir: Optional[str] = None,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process video through all agents.
        
        Args:
            video_path: Path to input video file
            output_dir: Directory for outputs (default: same as input)
            config_overrides: Optional config overrides
            
        Returns:
            {
                "final_video_path": str,
                "captions_srt_path": str,
                "thumbnail_paths": list[str],
                "processing_log_path": str,
                "total_time": float,
                "error_messages": list[str]
            }
        """
        start_time = time.time()
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")
        
        # Setup output directory
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = video_path.parent / f"{video_path.stem}_output"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"=" * 50)
        self.logger.info(f"🎬 Antigravity Video Pipeline")
        self.logger.info(f"   Input: {video_path.name}")
        self.logger.info(f"   Output: {output_dir}")
        self.logger.info(f"=" * 50)
        
        # Prepare config
        config = self._apply_overrides(config_overrides or {})
        config = self._apply_ci_safety(config)
        
        # Create agents
        agents = self._create_agents(config)
        
        # Run pipeline
        results = {}
        error_messages: List[str] = []
        fail_fast = config.get("pipeline", {}).get("fail_fast", False)
        
        # 1. Backup
        self.logger.info("\n📦 Phase 1: Backup")
        results["backup"] = agents["backup"].process(str(video_path), str(output_dir))
        
        # 2. Audio Processing
        self.logger.info("\n🎵 Phase 2: Audio Processing")
        results["audio"] = agents["audio"].process(str(video_path), str(output_dir))
        if not results["audio"]["success"]:
            error_messages.append(results["audio"].get("error", "Audio processing failed"))
            if fail_fast:
                return self._build_result(results, output_dir, time.time() - start_time, error_messages)
        
        # 3. Caption Generation
        self.logger.info("\n📝 Phase 3: Caption Generation")
        results["captions"] = agents["captions"].process(str(video_path), str(output_dir))
        if not results["captions"]["success"]:
            error_messages.append(results["captions"].get("error", "Caption generation failed"))
            if fail_fast:
                return self._build_result(results, output_dir, time.time() - start_time, error_messages)
        
        # 4. Video Enhancement (Merge Audio if available)
        self.logger.info("\n🎨 Phase 4: Video Enhancement")
        
        # Phase 3 Requirement: Merge media outputs
        # If we have normalized audio, we should use it for the video enhancement output
        video_config_overrides = {}
        processed_audio = results.get("audio", {}).get("output_path")
        
        if processed_audio:
            self.logger.info(f"   Merging processed audio: {Path(processed_audio).name}")
            # We inject the audio path as an override or extra arg
            # However, since BaseAgent interface is fixed, we can pass it via config or modify the agent to accept 'audio_track'
            # Let's use a config override approach for the agent to pick up
            video_config_overrides["external_audio_path"] = processed_audio

        # Apply temporary overrides to the agent instance
        original_video_config = agents["video"].config.copy()
        agents["video"].config.update(video_config_overrides)
        
        results["video"] = agents["video"].process(str(video_path), str(output_dir))
        
        # Restore config
        agents["video"].config = original_video_config
        
        if not results["video"]["success"]:
            error_messages.append(results["video"].get("error", "Video enhancement failed"))
            if fail_fast:
                return self._build_result(results, output_dir, time.time() - start_time, error_messages)
        
        # 5. Thumbnail Generation
        self.logger.info("\n🖼️  Phase 5: Thumbnail Generation")
        results["thumbnails"] = agents["thumbnails"].process(str(video_path), str(output_dir))
        if not results["thumbnails"]["success"]:
            error_messages.append(results["thumbnails"].get("error", "Thumbnail generation failed"))
        
        total_time = time.time() - start_time
        return self._build_result(results, output_dir, total_time, error_messages)
    
    def _build_result(
        self,
        results: Dict[str, Any],
        output_dir: Path,
        total_time: float,
        error_messages: List[str]
    ) -> Dict[str, Any]:
        """Build final result dict and save log."""
        
        # Save processing log
        log_path = self._save_processing_log(output_dir, results, total_time)
        
        # Build result
        result = {
            "final_video_path": results.get("video", {}).get("output_path"),
            "captions_srt_path": results.get("captions", {}).get("srt_path"),
            "thumbnail_paths": results.get("thumbnails", {}).get("thumbnail_paths", []),
            "processing_log_path": log_path,
            "total_time": round(total_time, 2),
            "error_messages": error_messages,
        }
        
        self.logger.info("\n" + "=" * 50)
        self.logger.info("📊 Pipeline Complete")
        self.logger.info(f"   Total time: {total_time:.1f}s")
        self.logger.info(f"   Errors: {len(error_messages)}")
        self.logger.info("=" * 50)
        
        return result
    
    def dry_run(self, video_path: str) -> Dict[str, Any]:
        """
        Validate inputs without processing.
        
        Returns config and validation status.
        """
        video_path = Path(video_path)
        
        self.logger.info("🔍 Dry run - validating only")
        
        checks = {
            "config_valid": True,
            "video_exists": video_path.exists(),
            "video_readable": video_path.is_file() if video_path.exists() else False,
            "ffmpeg_available": self._check_ffmpeg(),
            "whisper_available": self._check_whisper(),
        }
        
        self.logger.info(f"   Config valid: {'✅' if checks['config_valid'] else '❌'}")
        self.logger.info(f"   Video exists: {'✅' if checks['video_exists'] else '❌'}")
        self.logger.info(f"   FFmpeg: {'✅' if checks['ffmpeg_available'] else '❌'}")
        self.logger.info(f"   Whisper: {'✅' if checks['whisper_available'] else '❌'}")
        
        return {
            "checks": checks,
            "config": self.config,
            "all_passed": all(checks.values())
        }
    
    def _check_ffmpeg(self) -> bool:
        """Check if FFmpeg is available."""
        import subprocess
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, timeout=5)
            return True
        except Exception:
            return False
    
    def _check_whisper(self) -> bool:
        """Check if Whisper is available."""
        try:
            import whisper
            return True
        except ImportError:
            return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Antigravity Video Production Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s input.mp4
  %(prog)s input.mp4 --output-dir ./output
  %(prog)s input.mp4 --dry-run --verbose
  %(prog)s input.mp4 --config custom_config.json
        """
    )
    
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("--output-dir", "-o", help="Output directory")
    parser.add_argument("--config", "-c", help="Path to custom config JSON")
    parser.add_argument("--dry-run", "-n", action="store_true", 
                        help="Validate without processing")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    
    # Create orchestrator
    try:
        orchestrator = VideoPipelineOrchestrator(config_path=args.config)
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Run
    try:
        if args.dry_run:
            result = orchestrator.dry_run(args.video)
            if not result["all_passed"]:
                sys.exit(1)
        else:
            result = orchestrator.process(args.video, output_dir=args.output_dir)
            
            if result["error_messages"]:
                print(f"\n⚠️  Completed with {len(result['error_messages'])} error(s)")
                for err in result["error_messages"]:
                    print(f"   - {err}")
                sys.exit(1)
            else:
                print(f"\n✅ Success! Output: {result['final_video_path']}")
                
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
