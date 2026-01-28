import shutil
import os
import json
from fastapi import UploadFile
from typing import Dict, Any
from audio_engine.processor import run_job, TEMP_DIR

async def process_upload(file: UploadFile, preset_json: str) -> Dict[str, Any]:
    # Parse preset
    preset = json.loads(preset_json)
    
    # Save Upload
    temp_path = os.path.join(TEMP_DIR, file.filename)
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # Run Job
        report = run_job(temp_path, preset)
        return report
    finally:
        # Cleanup input (optional, maybe keep for debugging in early dev)
        # os.remove(temp_path)
        pass
