export interface LevelerAlgo {
    enabled: boolean;
    mode: string;
    strength_percent: number;
    compressor: string;
}

export interface FilteringAlgo {
    enabled: boolean;
    method: string;
}

export interface LoudnessAlgo {
    enabled: boolean;
    target_lufs: number;
    peak_mode: string; // 'auto' | 'fixed'
    true_peak_db: number;
    dual_mono: boolean;
    method: string;
}

export interface NoiseAlgo {
    enabled: boolean;
    denoise_method: string;
    remove_noise_amount: number | string; // 'auto' | 100 etc
    remove_reverb_amount: number | string;
    remove_breaths: string;
}

export interface CuttingAlgo {
    enabled: boolean;
}

export interface Algorithms {
    leveler: LevelerAlgo;
    filtering: FilteringAlgo;
    loudness: LoudnessAlgo;
    noise: NoiseAlgo;
    cutting: CuttingAlgo;
}

export interface Preset {
    chapters_text: string;
    algorithms: Algorithms;
}

export const DEFAULT_PRESET: Preset = {
    chapters_text: "",
    algorithms: {
        leveler: { enabled: true, mode: "default_leveler", strength_percent: 100, compressor: "auto" },
        filtering: { enabled: true, method: "voice_autoeq" },
        loudness: { enabled: true, target_lufs: -14, peak_mode: "auto", true_peak_db: -1.0, dual_mono: false, method: "program_loudness" },
        noise: { enabled: true, denoise_method: "dynamic", remove_noise_amount: 100, remove_reverb_amount: 100, remove_breaths: "off" },
        cutting: { enabled: false }
    }
};
