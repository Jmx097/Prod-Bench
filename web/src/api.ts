import type { Preset } from "./types";

const API_BASE = "http://localhost:8000";

export async function getPreset(name: string): Promise<Preset> {
    const res = await fetch(`${API_BASE}/presets/${name}`);
    if (!res.ok) throw new Error("Failed to load preset");
    return res.json();
}

export async function savePreset(name: string, preset: Preset): Promise<void> {
    const res = await fetch(`${API_BASE}/presets/${name}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(preset)
    });
    if (!res.ok) throw new Error("Failed to save preset");
}

export async function uploadAndProcess(file: File, preset: Preset) {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("preset", JSON.stringify(preset));

    const res = await fetch(`${API_BASE}/process_upload`, {
        method: "POST",
        body: formData
    });
    if (!res.ok) {
        const txt = await res.text();
        throw new Error("Processing failed: " + txt);
    }
    return res.json();
}
