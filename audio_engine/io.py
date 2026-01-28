import ffmpeg
import os
from typing import Dict, Any

def get_media_info(path: str) -> Dict[str, Any]:
    """
    Returns media info using ffprobe.
    """
    try:
        probe = ffmpeg.probe(path)
        # Find audio stream
        audio_streams = [s for s in probe['streams'] if s['codec_type'] == 'audio']
        if not audio_streams:
            raise ValueError("No audio stream found")
        
        info = audio_streams[0]
        format_info = probe['format']
        
        return {
            "duration": float(format_info.get('duration', 0)),
            "format_name": format_info.get('format_name'),
            "bit_rate": int(format_info.get('bit_rate', 0)) if format_info.get('bit_rate') else 0,
            "sample_rate": int(info.get('sample_rate', 0)),
            "channels": int(info.get('channels', 1)),
            "codec": info.get('codec_name')
        }
    except ffmpeg.Error as e:
        print("ffmpeg error:", e.stderr)
        raise
