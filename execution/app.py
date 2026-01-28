import streamlit as st
import json
import shutil
import time
from pathlib import Path
import tempfile
import sys
import os

# Add parent dir to path to import execution module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.antigravity_pipeline import VideoPipelineOrchestrator

st.set_page_config(
    page_title="Antigravity Pipeline",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 Antigravity Video Production Pipeline")
st.markdown("Automated video post-production: Audio Norm, Captions, Color Grade, and more.")

# --- Sidebar Config ---
st.sidebar.header("Configuration")

# Audio Config
st.sidebar.subheader("🔊 Audio")
lufs = st.sidebar.slider("Target LUFS", -30, -5, -14, help="Loudness target (default -14)")
noise_reduction = st.sidebar.checkbox("Noise Reduction", value=False)

# Caption Config
st.sidebar.subheader("📝 Captions")
burn_captions = st.sidebar.checkbox("Burn Captions into Video", value=False)
whisper_model = st.sidebar.selectbox("Whisper Model", ["tiny", "base", "small", "medium", "large"], index=1)
max_words = st.sidebar.number_input("Max Words per Line", 5, 20, 10)

# Video Config
st.sidebar.subheader("🎨 Video")
crf = st.sidebar.slider("Quality (CRF)", 0, 51, 18, help="Lower is better quality")
upscale = st.sidebar.checkbox("Upscale (Stub)", value=False)
backup_drive = st.sidebar.checkbox("Backup to Drive (Stub)", value=False)

# --- Main Interface ---

uploaded_file = st.file_uploader("Upload a video", type=["mp4", "mov", "mkv"])

if uploaded_file:
    st.video(uploaded_file)
    
    if st.button("🚀 Run Pipeline", type="primary"):
        # Create temp environment
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            tmp_path = Path(tmp_dir_name)
            
            # Save uploaded file
            input_path = tmp_path / uploaded_file.name
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Setup Config Override
            overrides = {
                "audio": {
                    "target_loudness_lufs": lufs,
                    "noise_reduction": noise_reduction
                },
                "captions": {
                    "whisper_model": whisper_model,
                    "burn_captions": burn_captions,
                    "max_words_per_line": max_words
                },
                "video": {
                    "crf": crf,
                    "upscale": upscale
                },
                "backup": {
                    "upload_to_drive": backup_drive
                }
            }
            
            # Save config for orchestrator
            config_path = tmp_path / "ui_config.json"
            # We'll rely on the orchestrator correctly merging defaults, 
            # but we need to pass overrides differently or write a full config.
            # The CLI supports a config path. We'll write a full merged config or just rely on defaults + overrides 
            # if we modified the orchestrator to accept dict overrides. 
            # The orchestrator `process` method accepts `config_overrides`!
            # But the `__init__` loads the base config.
            
            # We will init orchestrator with default config, then pass overrides to process()
            orchestrator = VideoPipelineOrchestrator() # Loads default production_config.json
            
            # Create output dir
            output_dir = Path("output_web") / f"run_{int(time.time())}"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            status_container = st.container()
            with status_container:
                st.info("🔄 Processing... check terminal for detailed FFmpeg logs")
                
                # Progress Bar (Simulated as stages)
                progress_bar = st.progress(0)
                
                # Run Processing
                try:
                    start_time = time.time()
                    
                    # Hack: The orchestrator logs to file/console. We can't easily capture it here without piping 
                    # but we can show final result.
                    
                    with st.spinner("Agents working..."):
                        result = orchestrator.process(
                            str(input_path), 
                            str(output_dir), 
                            config_overrides=overrides
                        )
                    
                    progress_bar.progress(100)
                    
                    if result["success"]:
                        st.success(f"✅ Pipeline Complete in {result['total_time']:.1f}s")
                        
                        # Display Results
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("📺 Output Video")
                            if "final_video_path" in result and Path(result["final_video_path"]).exists():
                                st.video(str(result["final_video_path"]))
                            else:
                                st.warning("No video output found.")
                                
                        with col2:
                            st.subheader("📄 Assets")
                            if "captions_srt_path" in result:
                                with open(result["captions_srt_path"]) as f:
                                    st.download_button("Download Captions (.srt)", f, "captions.srt")
                                    
                            if "audio_normalized_path" in result and Path(result["audio_normalized_path"]).exists():
                                with open(result["audio_normalized_path"], "rb") as f:
                                    st.download_button("Download Audio (.wav)", f, "audio.wav")
                            
                            st.caption("Thumbnails:")
                            if "thumbnail_paths" in result:
                                cols = st.columns(3)
                                for i, thumb_path in enumerate(result["thumbnail_paths"]):
                                    with cols[i % 3]:
                                        st.image(thumb_path, use_container_width=True)
                        
                        # Logs
                        with st.expander("View Processing Log"):
                            st.json(result)
                            
                    else:
                        st.error("❌ Processing Failed")
                        st.write(result["error_messages"])
                        
                except Exception as e:
                    st.error(f"Critical Error: {e}")
