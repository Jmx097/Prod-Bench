import os
import shutil
import uuid
import logging
from typing import Dict, Any
from .loudness import normalize_audio
from .metrics import measure_loudness

logger = logging.getLogger(__name__)

TEMP_DIR = os.path.join(os.path.dirname(__file__), "..", "temp")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_job(input_path: str, preset: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrates the processing job:
    1. Reads preset config
    2. Runs pipeline (currently just Loudness)
    3. Generates report
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Starting job {job_id} for {input_path}")
    
    # Determine targets
    loudness_algo = preset.get('algorithms', {}).get('loudness', {})
    target_lufs = float(loudness_algo.get('target_lufs', -14))
    
    # Peak mode handling
    peak_mode = loudness_algo.get('peak_mode', 'auto')
    fixed_peak = float(loudness_algo.get('true_peak_db', -1.0))
    
    if peak_mode == 'auto':
        # Prompt rule: -1 dBTP for -14, -2 dBTP for -16 or lower
        if target_lufs <= -16:
            true_peak = -2.0
        else:
            true_peak = -1.0
    else:
        true_peak = fixed_peak

    # Prepare output path
    filename = os.path.basename(input_path)
    output_filename = f"processed_{filename}"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Execute Pipeline
    # M1: Just Loudness Normalization
    if loudness_algo.get('enabled', True):
        # We start with normalization
        # Note: In a full chain, this is usually last. But for M1 it's the only step.
        initial_measurements = normalize_audio(
            input_path=input_path,
            output_path=output_path,
            target_lufs=target_lufs,
            true_peak=true_peak,
            dual_mono=loudness_algo.get('dual_mono', False)
        )
    else:
        # Just copy if disabled (unlikely for "Loudness Normalization" focus, but good for robustness)
        shutil.copy(input_path, output_path)
        initial_measurements = measure_loudness(input_path) # measure anyway for report

    # Measure Output for verification
    final_measurements = measure_loudness(output_path)
    
    # Construct Report
    return {
        "job_id": job_id,
        "input": {
            "file": filename,
            "lufs": float(initial_measurements['input_i']),
            "true_peak": float(initial_measurements['input_tp']),
            "lra": float(initial_measurements['input_lra'])
        },
        "output": {
            "file": output_filename,
            "path": output_path, # Local path for now
            "lufs": float(final_measurements['input_i']),
            "true_peak": float(final_measurements['input_tp']),
            "lra": float(final_measurements['input_lra'])
        },
        "targets": {
            "lufs": target_lufs,
            "true_peak": true_peak
        }
    }
