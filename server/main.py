from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from server import preset_store

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PresetModel(BaseModel):
    chapters_text: str
    algorithms: Dict[str, Any]

@app.get("/presets")
def list_presets():
    return {"presets": preset_store.list_preset_names()}

@app.get("/presets/{name}")
def get_preset(name: str):
    preset = preset_store.get_preset(name)
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    return preset

@app.post("/presets/{name}")
def save_preset(name: str, preset: PresetModel):
    preset_store.update_preset(name, preset.dict())
    return {"status": "saved", "name": name}

@app.post("/process_upload")
async def run_process_upload(file: UploadFile = File(...), preset: str = Form(...)):
    """
    Accepts a file upload and a JSON string 'preset'.
    """
    from server.job_runner import process_upload
    return await process_upload(file, preset)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
