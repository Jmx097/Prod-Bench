#!/usr/bin/env python3
"""
Caption Generator Agent - Transcribes audio and generates SRT subtitles.

Uses OpenAI Whisper for speech-to-text with word-level timestamps.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Tuple
import tempfile

from .base_agent import BaseAgent


class CaptionGeneratorAgent(BaseAgent):
    """
    Generates SRT captions using Whisper transcription.
    
    Config keys:
        whisper_model: Model size (tiny, base, small, medium, large)
        language: ISO 639-1 language code 
        max_words_per_line: Maximum words per subtitle line
        max_chars_per_line: Maximum characters per line
        burn_captions: Burn captions into video (default: False)
        font_size: Font size for burned captions (default: 24)
        font_color: Font color for burned captions (default: 'white')
    """
    
    def _extract_audio(self, video_path: Path, audio_path: Path) -> None:
        """Extract audio from video for Whisper processing."""
        cmd = [
            "ffmpeg", "-y", "-hide_banner",
            "-i", str(video_path),
            "-vn",
            "-ar", "16000",  # Whisper expects 16kHz
            "-ac", "1",  # Mono
            "-c:a", "pcm_s16le",
            "-loglevel", "error",
            str(audio_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            raise RuntimeError(f"Audio extraction failed: {result.stderr}")
    

    def _transcribe(self, audio_path: Path) -> List[Dict[str, Any]]:
        """Transcribe audio using Whisper (Local or API)."""
        use_api = self.config.get("use_api", False)
        
        if use_api:
            return self._transcribe_api(audio_path)
        else:
            return self._transcribe_local(audio_path)

    def _transcribe_api(self, audio_path: Path) -> List[Dict[str, Any]]:
        """Transcribe using OpenAI API."""
        try:
            from openai import OpenAI
            import os
            from dotenv import load_dotenv
            
            # Load environment variables (to ensure OPENAI_API_KEY is available)
            load_dotenv()
            
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
                
            client = OpenAI(api_key=api_key)
            model_name = "whisper-1" # Standard API model
            
            self.logger.info(f"Transcribing via OpenAI API ({model_name})...")
            
            with open(audio_path, "rb") as audio_file:
                # Note: API response format for 'verbose_json' matches internal structure roughly
                transcript = client.audio.transcriptions.create(
                    model=model_name,
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"] # Request word timestamps
                )
            
            # Convert API response object to dictionary format expected by segment logic
            api_segments = transcript.segments
            api_words = transcript.words
            
            normalized_segments = []
            
            # Pool of all words (convert from Pydantic models if needed)
            words_pool = [w.model_dump() for w in api_words] if hasattr(api_words[0], 'model_dump') else api_words
            
            for seg in api_segments:
                seg_dict = seg.model_dump() if hasattr(seg, 'model_dump') else seg
                
                # Filter words that belong to this segment
                seg_start = seg_dict['start']
                seg_end = seg_dict['end']
                
                # Assign words to segment if not present or empty
                if 'words' not in seg_dict or not seg_dict['words']:
                    seg_dict['words'] = [
                        w for w in words_pool 
                        if w['start'] >= seg_start and w['end'] <= seg_end
                    ]
                
                normalized_segments.append(seg_dict)
                
            return normalized_segments

        except ImportError:
            raise RuntimeError("openai or python-dotenv package not installed. Run 'pip install openai python-dotenv'")
        except Exception as e:
            raise RuntimeError(f"OpenAI API Transcription failed: {e}")

    def _transcribe_local(self, audio_path: Path) -> List[Dict[str, Any]]:
        """Transcribe using local Whisper library."""
        import whisper
        
        model_name = self.config.get("whisper_model", "base")
        language = self.config.get("language", "en")
        
        self.logger.info(f"Loading Whisper model (Local): {model_name}")
        model = whisper.load_model(model_name)
        
        self.logger.info("Transcribing audio (Local)...")
        result = model.transcribe(
            str(audio_path),
            language=language,
            word_timestamps=True
        )
        
        return result.get("segments", [])

    
    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format (HH:MM:SS,mmm)."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _segment_to_srt_lines(self, segment: Dict[str, Any]) -> List[Tuple[float, float, str]]:
        """
        Break a segment into multiple SRT entries based on word limits.
        
        Returns list of (start, end, text) tuples.
        """
        max_words = self.config.get("max_words_per_line", 10)
        max_chars = self.config.get("max_chars_per_line", 42)
        
        words = segment.get("words", [])
        if not words:
            # Fallback to segment-level timing
            return [(segment["start"], segment["end"], segment["text"].strip())]
        
        lines = []
        current_words = []
        current_start = None
        current_end = None
        
        for word_info in words:
            word = word_info.get("word", "").strip()
            if not word:
                continue
            
            if current_start is None:
                current_start = word_info["start"]
            
            current_words.append(word)
            current_end = word_info["end"]
            
            current_text = " ".join(current_words)
            
            # Check if we should start a new line
            if len(current_words) >= max_words or len(current_text) >= max_chars:
                lines.append((current_start, current_end, current_text))
                current_words = []
                current_start = None
                current_end = None
        
        # Add remaining words
        if current_words:
            lines.append((current_start, current_end, " ".join(current_words)))
        
        return lines
    
    def _generate_srt(self, segments: List[Dict[str, Any]], output_path: Path) -> Dict[str, Any]:
        """Generate SRT file from transcription segments."""
        srt_entries = []
        word_count = 0
        
        for segment in segments:
            lines = self._segment_to_srt_lines(segment)
            srt_entries.extend(lines)
            word_count += len(segment.get("text", "").split())
        
        # Write SRT file
        with open(output_path, "w", encoding="utf-8") as f:
            for i, (start, end, text) in enumerate(srt_entries, 1):
                f.write(f"{i}\n")
                f.write(f"{self._format_timestamp(start)} --> {self._format_timestamp(end)}\n")
                f.write(f"{text}\n\n")
        
        duration = srt_entries[-1][1] if srt_entries else 0
        
        return {
            "entry_count": len(srt_entries),
            "word_count": word_count,
            "duration": duration
        }
    
    def _burn_captions(self, video_path: str, srt_path: str, output_path: str):
        """Burn captions into video using FFmpeg."""
        # Note: formatting srt path for ffmpeg filter requires escaping
        # simple replacement for Windows path backslashes often needed
        srt_path_escaped = srt_path.replace("\\", "/").replace(":", "\\:")
        
        font_size = self.config.get('font_size', 24)
        font_color = self.config.get('font_color', '&HFFFFFF&')
        
        filter_str = f"subtitles='{srt_path_escaped}':force_style='FontSize={font_size},PrimaryColour={font_color}'"
        
        cmd = [
            "ffmpeg", "-y", "-i", video_path,
            "-vf", filter_str,
            "-c:a", "copy",
            "-c:v", "libx264", # Ensure compatibility
            output_path
        ]
        
        self.logger.info(f"Burning captions: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, capture_output=True)

    def _execute(self, input_path: Path, output_dir: Path) -> Dict[str, Any]:
        """
        Generate SRT captions from video and optionally burn them.
        """
        self.validate_input(input_path)
        
        output_path = output_dir / f"{input_path.stem}_captions.srt"
        
        # Extract audio to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = Path(tmp.name)
        
        try:
            self.logger.info(f"Extracting audio from {input_path.name}")
            self._extract_audio(input_path, audio_path)
            
            # Transcribe
            segments = self._transcribe(audio_path)
            
            # Generate SRT
            self.logger.info(f"Generating SRT file: {output_path.name}")
            stats = self._generate_srt(segments, output_path)
            
            result = {
                "srt_path": str(output_path),
                **stats
            }
            
            # Burn captions if requested
            if self.config.get("burn_captions"):
                 burned_video_path = output_dir / f"{input_path.stem}_burned.mp4"
                 self.logger.info(f"Burning captions into video: {burned_video_path.name}")
                 self._burn_captions(str(input_path), str(output_path), str(burned_video_path))
                 result["burned_video_path"] = str(burned_video_path)
            
        finally:
            # Cleanup temp audio
            if audio_path.exists():
                audio_path.unlink()
        
        if not output_path.exists():
            raise RuntimeError("SRT file was not created")
        
        self.logger.info(f"Captions generated: {stats['entry_count']} entries, {stats['word_count']} words")
        
        return result
