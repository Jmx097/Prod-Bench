import { useEffect, useState } from "react";
import type { Algorithms, Preset } from "../types";
import { DEFAULT_PRESET } from "../types";
import * as api from "../api";
import { Card, CardBody, CardHeader, Checkbox, Label, Select } from "../components/ui";

const PRESET_NAME = "youtube_voice_default";

export default function PresetEditor() {
    const [preset, setPreset] = useState<Preset>(DEFAULT_PRESET);
    const [loading, setLoading] = useState(true);
    const [processing, setProcessing] = useState(false);

    useEffect(() => {
        api.getPreset(PRESET_NAME).then(p => {
            setPreset(p);
            setLoading(false);
        }).catch(err => {
            console.error(err);
            setLoading(false);
        });
    }, []);

    const updateAlgo = <K extends keyof Algorithms>(key: K, data: Partial<Algorithms[K]>) => {
        setPreset(p => ({
            ...p,
            algorithms: {
                ...p.algorithms,
                [key]: { ...p.algorithms[key], ...data }
            }
        }));
    };

    const handleSave = async () => {
        try {
            await api.savePreset(PRESET_NAME, preset);
            alert("Preset Saved!");
        } catch (e) {
            alert("Error saving preset");
        }
    };

    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const handleRun = async () => {
        if (!selectedFile) {
            alert("Please select a file first");
            return;
        }
        setProcessing(true);
        try {
            const res = await api.uploadAndProcess(selectedFile, preset);
            alert("Processing Complete!\n\n" +
                  `Input: ${res.input.lufs.toFixed(1)} LUFS, ${res.input.true_peak.toFixed(1)} dBTP\n` +
                  `Output: ${res.output.lufs.toFixed(1)} LUFS, ${res.output.true_peak.toFixed(1)} dBTP\n` +
                  `File: ${res.output.path}`
            );
        } catch (err: any) {
            alert("Error: " + err.message);
        } finally {
            setProcessing(false);
        }
    };

    if (loading) return <div className="p-8">Loading...</div>;

    const { leveler, filtering, loudness, noise, cutting } = preset.algorithms;

    return (
        <div className="max-w-4xl mx-auto p-6 space-y-6">
            <header className="flex justify-between items-end border-b pb-4">
                <div>
                    <h5 className="text-gray-500 text-sm">auphonic.com / Preset</h5>
                    <div className="text-2xl font-bold flex items-center gap-2">
                        {PRESET_NAME} <span className="text-xs font-normal text-gray-400">(editing)</span>
                    </div>
                </div>
            </header>
            
            <div className="bg-blue-50 border border-blue-200 p-4 rounded">
                <Label>Input File (for local running)</Label>
                <input type="file" onChange={e => setSelectedFile(e.target.files?.[0] || null)} />
            </div>

            {/* Chapters */}
            <section className="bg-white border rounded shadow-sm p-4">
                <div className="mb-2 font-mono text-sm text-gray-500">Chapters</div>
                <textarea
                    className="w-full font-mono text-sm border p-2 h-32"
                    value={preset.chapters_text}
                    onChange={e => setPreset({ ...preset, chapters_text: e.target.value })}
                />
            </section>

            {/* Algorithms */}
            <section>
                <div className="flex justify-between items-center mb-2">
                    <h3 className="font-bold text-lg">Audio Algorithms</h3>
                </div>

                {/* Leveler */}
                <Card>
                    <CardHeader>
                        <Checkbox label="Adaptive Leveler" checked={leveler.enabled} onChange={e => updateAlgo('leveler', { enabled: e.target.checked })} />
                        {leveler.enabled && (
                            <div className="flex items-center gap-2">
                                <span className="text-sm text-gray-600">Mode:</span>
                                <Select value={leveler.mode} onChange={e => updateAlgo('leveler', { mode: e.target.value })}>
                                    <option value="default_leveler">Default Leveler</option>
                                    <option value="fast_leveler">Fast Leveler</option>
                                </Select>
                            </div>
                        )}
                    </CardHeader>
                    {leveler.enabled && (
                        <CardBody className="grid grid-cols-2 gap-6">
                            <div>
                                <Label>Leveler Strength</Label>
                                <Select value={leveler.strength_percent} onChange={e => updateAlgo('leveler', { strength_percent: parseInt(e.target.value) })}>
                                    <option value={100}>100% (Default)</option>
                                    <option value={80}>80%</option>
                                    <option value={120}>120%</option>
                                </Select>
                            </div>
                            <div>
                                <Label>Compressor</Label>
                                <Select value={leveler.compressor} onChange={e => updateAlgo('leveler', { compressor: e.target.value })}>
                                    <option value="auto">Auto</option>
                                    <option value="off">Off</option>
                                    <option value="hard">Hard</option>
                                </Select>
                            </div>
                        </CardBody>
                    )}
                </Card>

                {/* Filtering */}
                <Card>
                    <CardHeader>
                        <Checkbox label="Filtering" checked={filtering.enabled} onChange={e => updateAlgo('filtering', { enabled: e.target.checked })} />
                        {filtering.enabled && (
                             <Select className="w-48" value={filtering.method} onChange={e => updateAlgo('filtering', { method: e.target.value })}>
                                <option value="voice_autoeq">Voice AutoEQ</option>
                                <option value="hpf">High-pass Only</option>
                             </Select>
                        )}
                    </CardHeader>
                </Card>

                {/* Loudness */}
                <Card>
                    <CardHeader>
                        <Checkbox label="Loudness Normalization" checked={loudness.enabled} onChange={e => updateAlgo('loudness', { enabled: e.target.checked })} />
                    </CardHeader>
                    {loudness.enabled && (
                        <CardBody className="grid grid-cols-4 gap-4">
                            <div>
                                <Label>Loudness Target</Label>
                                <Select value={loudness.target_lufs} onChange={e => updateAlgo('loudness', { target_lufs: parseInt(e.target.value) })}>
                                    <option value={-14}>-14 LUFS</option>
                                    <option value={-16}>-16 LUFS</option>
                                    <option value={-23}>-23 LUFS</option>
                                </Select>
                            </div>
                            <div>
                                <Label>Max Peak Level</Label>
                                <Select value={loudness.peak_mode} onChange={e => updateAlgo('loudness', { peak_mode: e.target.value })}>
                                    <option value="auto">Auto</option>
                                    <option value="fixed_1">-1 dBTP</option>
                                </Select>
                            </div>
                            <div className="flex items-end pb-2">
                                <Checkbox label="Dual Mono" checked={loudness.dual_mono} onChange={e => updateAlgo('loudness', { dual_mono: e.target.checked })} />
                            </div>
                            <div>
                                <Label>Norm. Method</Label>
                                <Select value={loudness.method} onChange={e => updateAlgo('loudness', { method: e.target.value })}>
                                    <option value="program_loudness">Program Loudness</option>
                                </Select>
                            </div>
                        </CardBody>
                    )}
                </Card>

                 {/* Noise */}
                 <Card>
                    <CardHeader>
                        <Checkbox label="Noise Reduction" checked={noise.enabled} onChange={e => updateAlgo('noise', { enabled: e.target.checked })} />
                    </CardHeader>
                    {noise.enabled && (
                        <CardBody className="grid grid-cols-4 gap-4">
                            <div className="col-span-2">
                                <Label>Denoising Method</Label>
                                <Select value={noise.denoise_method} onChange={e => updateAlgo('noise', { denoise_method: e.target.value })}>
                                    <option value="dynamic">Dynamic: keep speech...</option>
                                    <option value="speech_only">Speech only</option>
                                </Select>
                            </div>
                             <div>
                                <Label>Remove Noise</Label>
                                <Select value={noise.remove_noise_amount} onChange={e => updateAlgo('noise', { remove_noise_amount: e.target.value })}>
                                    <option value={100}>100 dB (full)</option>
                                    <option value={10}>10 dB</option>
                                </Select>
                            </div>
                        </CardBody>
                    )}
                </Card>

                {/* Cutting */}
                 <Card>
                    <CardHeader>
                        <Checkbox label="Automatic Cutting" checked={cutting.enabled} onChange={e => updateAlgo('cutting', { enabled: e.target.checked })} />
                    </CardHeader>
                </Card>

            </section>

             <div className="fixed bottom-0 left-0 right-0 bg-white border-t p-4 flex justify-end gap-4 shadow-lg">
                <button
                    onClick={handleRun}
                    className="px-6 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200"
                    disabled={processing}
                >
                    {processing ? "Processing..." : "Run Processing"}
                </button>
                <button
                    onClick={handleSave}
                    className="px-6 py-2 bg-red-600 text-white rounded hover:bg-red-700 font-bold"
                >
                    Save Preset
                </button>
            </div>
            <div className="h-20"></div>
        </div>
    );
}
