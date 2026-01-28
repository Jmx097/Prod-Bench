import ffmpeg
from .metrics import measure_loudness
import logging

logger = logging.getLogger(__name__)

def normalize_audio(input_path: str, output_path: str, target_lufs: float = -14.0, true_peak: float = -1.0, dual_mono: bool = False):
    """
    Performs 2-pass Loudness Normalization to meet target_lufs and true_peak.
    """
    
    # Pass 1: Measure
    logger.info(f"Measuring {input_path}...")
    measurements = measure_loudness(input_path)
    
    logger.info(f"Measurements: {measurements}")
    
    # Pass 2: Apply
    # We feed the measured values back into loudnorm
    # Note: 'dual_mono' is not directly a loudnorm param, it usually implies treating channels independently.
    # Standard loudnorm works on the integrated stream. 
    # For v1 we adhere to standard coupled normalization.
    
    # FFmpeg loudnorm params:
    # I: integrated loudness target
    # TP: max true peak target
    # LRA: loudness range target (default 7.0 is usually fine for speech, but we can stick to defaults)
    # measured_I, measured_TP, measured_LRA, measured_thresh from pass 1
    
    stream = ffmpeg.input(input_path)
    
    loudnorm_params = {
        'I': target_lufs,
        'TP': true_peak,
        'measured_I': measurements['input_i'],
        'measured_TP': measurements['input_tp'],
        'measured_LRA': measurements['input_lra'],
        'measured_thresh': measurements['input_thresh'],
        'offset': measurements['target_offset'],
        'linear': 'true', # linear normalization recommended for 2nd pass
        'print_format': 'summary'
    }
    
    if dual_mono:
        # TODO: Split channels, norm independently, merge. Complex filter graph.
        # For M1 we skip strictly implementing dual mono and log a warning
        logger.warning("Dual Mono requested but not yet implemented in M1. Using stereo coupled.")
        
    stream = ffmpeg.filter(stream, 'loudnorm', **loudnorm_params)
    
    # Output
    # We use a standard high quality audio codec, e.g., aac or just copy container default if wav
    # For simplicity, if output ends in .mp3 use libmp3lame, if .wav use pcm_s24le or similar
    
    output_kwargs = {}
    if output_path.endswith('.mp3'):
        output_kwargs['acodec'] = 'libmp3lame'
        output_kwargs['audio_bitrate'] = '256k'
    elif output_path.endswith('.wav'):
        # preserve high quality
        pass
    
    stream = ffmpeg.output(stream, output_path, **output_kwargs)
    ffmpeg.run(stream, overwrite_output=True)
    
    return measurements
