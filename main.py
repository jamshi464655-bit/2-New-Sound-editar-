import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
import os
import zipfile
from io import BytesIO
import numpy as np
from scipy.io import wavfile
import soundfile as sf  # സ്ട്രീംലിറ്റിൽ ഓഡിയോ റീഡ് ചെയ്യാൻ സഹായിക്കുന്നു

# --- ഓഡിയോ പ്രോസസ്സിംഗ് ഫങ്ക്ഷൻ (Using SciPy) ---
def apply_studio_effects_scipy(input_filename, bass, treble, speed_factor):
    # ഓഡിയോ ഫയൽ റീഡ് ചെയ്യുന്നു
    data, samplerate = sf.read(input_filename)
    
    # സ്റ്റീരിയോ ആണെങ്കിൽ ഒരു ചാനൽ മാത്രമായി എടുക്കുന്നു (Mono)
    if len(data.shape) > 1:
        data = data[:, 0]
        
    # നൊർമലൈസേഷൻ (Normalize)
    if np.max(np.abs(data)) > 0:
        data = data / np.max(np.abs(data))

    # ലളിതമായ ബാസ്സ്/ട്രബിൾ ഇഫക്റ്റ് ഫിൽട്ടറിംഗ് (Simple Digital Filter)
    # ബാസ്സ് കൂട്ടാൻ (Low-pass smoothing)
    if bass > 0:
        bass_gain = (bass / 12.0) * 0.3
        smooth_data = np.convolve(data, np.ones(5)/5, mode='same')
        data = data + (smooth_data * bass_gain)
        
    # ട്രബിൾ കൂട്ടാൻ (High-pass sharpening)
    if treble > 0:
        treble_gain = (treble / 12.0) * 0.2
        sharp_data = data - np.convolve(data, np.ones(3)/3, mode='same')
        data = data + (sharp_data * treble_gain)

    # സ്പീഡ് കൺട്രോൾ
    if speed_factor != 1.0:
        samplerate = int(samplerate * speed_factor)

    # വീണ്ടും ഫയലിലേക്ക് സേവ് ചെയ്യുന്നു
    sf.write(input_filename, data, samplerate, format='MP3', bitrate=192)

async def edge_tts_generate(text, voice, output_filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)

def generate_google_tts(text, lang, output_filename):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_filename)

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Studio TTS", layout="wide")
st.title("🎙️ Roshan Pro Audio Studio & TTS Splitter")

left_col, right_col = st.columns([1.2, 1])

with left_col:
    st.write("### 📝 Text Input & Voice")
    text_input = st.text_area("നിങ്ങളുടെ ലോങ്ങ് ടെക്സ്റ്റ് ഇവിടെ പേസ്റ്റ് ചെയ്യുക:", height=250)
    
    voice_option = st.selectbox(
        "ഏത് വോയ്സ് വേണം?",
        options=[
            ("Microsoft Midhun (Male - Natural)", "edge_midhun"),
            ("Microsoft Sobhana (Female - Natural)", "edge_sobhana"),
            ("Google Malayalam (Female - Free)", "google_ml"),
            ("Microsoft US Ava (English)", "edge_en_ava"),
        ],
        format_func=lambda x: x[0]
    )

with right_col:
    st.write("### 🎛️ Studio Editing Console")
    bass_val = st.slider("🔊 Bass Booster", min_value=0, max_value=12, value=4, step=1)
    treble_val = st.slider("✨ Treble Enhancer", min_value=0, max_value=12, value=4, step=1)
    speed_val = st.slider("⏱️ Speed Factor", min_value=0.7, max_value=1.5, value=1.0, step=0.05)

st.write("---")

if st.button("🚀 Process & Generate Studio Audio", type="primary", use_container_width=True):
    if not text_input.strip():
        st.warning("ദയവായി ടെക്സ്റ്റ് ബോക്സിൽ എന്തെങ്കിലും ടെക്സ്റ്റ് നൽകുക.")
    else:
        paragraphs = [p.strip() for p in text_input.split("\n") if p.strip()]
        st.info(f"📋 ആകെ {len(paragraphs)} പാരഗ്രാഫുകൾ കണ്ടെത്തി. പ്രൊസസ്സിംഗ് ആരംഭിക്കുന്നു...")
        
        generated_files = []
        progress_bar = st.progress(0)
        
        for index, paragraph in enumerate(paragraphs):
            filename = f"studio_paragraph_{index + 1}.mp3"
            
            # TTS ജനറേഷൻ
            if voice_option[1] == "edge_midhun":
                asyncio.run(edge_tts_generate(paragraph, "ml-IN-MidhunNeural", filename))
            elif voice_option[1] == "edge_sobhana":
                asyncio.run(edge_tts_generate(paragraph, "ml-IN-SobhanaNeural", filename))
            elif voice_option[1] == "google_ml":
                generate_google_tts(paragraph, "ml", filename)
            elif voice_option[1] == "edge_en_ava":
                asyncio.run(edge_tts_generate(paragraph, "en-US-AvaNeural", filename))
                
            # പുതിയ രീതിയിലുള്ള എഫക്റ്റുകൾ നൽകുന്നു
            try:
                apply_studio_effects_scipy(filename, bass=bass_val, treble=treble_val, speed_factor=speed_val)
            except Exception as e:
                st.error(f"Error in Paragraph {index+1}: {e}")
                
            generated_files.append(filename)
            progress_bar.progress((index + 1) / len(paragraphs))
            
        st.success("🎯 എല്ലാ ഓഡിയോകളും വിജയകരമായി തയ്യാറായി കഴിഞ്ഞു!")
        
        st.write("### 🎧 Listen Mastered Tracks")
        play_col1, play_col2 = st.columns(2)
        for i, file in enumerate(generated_files):
            target_col = play_col1 if i % 2 == 0 else play_col2
            with target_col:
                st.write(f"🎵 **Track {i+1}**")
                st.audio(file, format="audio/mp3")
            
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in generated_files:
                zip_file.write(file)
                if os.path.exists(file):
                    os.remove(file)
                
        st.write("---")
        st.download_button(
            label="📦 Download All Mastered Audios (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="roshan_studio_outputs.zip",
            mime="application/zip",
            use_container_width=True
        )
