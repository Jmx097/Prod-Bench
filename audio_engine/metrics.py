import ffmpeg
import json
import logging
import sys

# Configure logging to capture ffmpeg output if needed
logger = logging.getLogger(__name__)

def measure_loudness(path: str) -> dict:
    """
    Runs a 1st pass loudnorm filter to measure Input Integrated Loudness, True Peak, LRA, and Threshold.
    Returns a dict with keys: input_i, input_tp, input_lra, input_thresh, target_offset.
    """
    try:
        # We run the loudnorm filter with print_format=json.
        # It doesn't output a file, so we map to null.
        # We must capture stderr to get the json output.
        stream = ffmpeg.input(path)
        stream = ffmpeg.output(stream, '-', f='null', af='loudnorm=print_format=json')
        out, err = ffmpeg.run(stream, capture_stdout=True, capture_stderr=True)
        
        # Parse stderr for the JSON block
        stderr_output = err.decode('utf-8')
        
        # The JSON output is usually at the end of stderr
        # We look for the formatted json structure
        lines = stderr_output.split('\n')
        json_str = ""
        in_json = False
        for line in lines:
            if line.strip() == '{':
                in_json = True
                json_str += "{\n"
                continue
            if in_json:
                json_str += line + "\n"
                if line.strip() == '}':
                    break
        
        if not json_str:
            logger.error(f"Could not find JSON in ffmpeg output: {stderr_output}")
            raise ValueError("Could not measure loudness: No JSON output from ffmpeg")
            
        data = json.loads(json_str)
        return data
        
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg Error: {e.stderr.decode('utf-8') if e.stderr else 'Unknown'}")
        raise
