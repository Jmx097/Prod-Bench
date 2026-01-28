import yaml
import os
from typing import Dict, Any, List

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "auphonic_presets.yaml")

def load_presets() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("presets", {})

def save_presets(presets: Dict[str, Any]):
    # ensure dir exists
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.safe_dump({"presets": presets}, f, default_flow_style=False, sort_keys=False)

def get_preset(name: str) -> Dict[str, Any] | None:
    presets = load_presets()
    return presets.get(name)

def update_preset(name: str, data: Dict[str, Any]):
    presets = load_presets()
    presets[name] = data
    save_presets(presets)

def list_preset_names() -> List[str]:
    presets = load_presets()
    return list(presets.keys())
