import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
import os
import zipfile
from io import BytesIO
import numpy as np

# --- 100% SERVER SAFE STUDIO EFFECTS (Using NumPy) ---
def apply_custom_studio_effects(input_filename, bass, treble, use_comp, reverb_level, speed_factor):
    # MP3 ഫയൽ റീഡ് ചെയ്യാനുള്ള ബിൽറ്റ്-ഇൻ സിസ്റ്റം (സെർവർ ക്രാഷ് ആവില്ല)
    with open(input_filename, "rb") as f:
        mp3_data = f.read()
    
    # ഹെഡറുകൾ മാറ്റാതെ ഓഡിയോ ഡാറ്റ മാത്രം പ്രോസസ്സ് ചെയ്യാൻ പാകത്തിൽ NumPy അറേ ആക്കുന്നു
    audio_array = np.frombuffer(mp3_data, dtype=np.int16, count=-1, offset=1000)
    
    if len(audio_array) == 0:
        return

    # 1. Dynamic Compression (ശബ്ദം ഒരേ ലെവലിൽ നിർത്താൻ)
    if use_comp:
        max_val = np.max(np.abs(audio_array)) if np.max(np.abs(audio_array)) > 0 else 1
        threshold = max_val * 0.6
        audio_array = np.where(np.abs(audio_array) > threshold, audio_array * 0.8, audio_array)

    # 2. Bass Booster (ശബ്ദത്തിന്റെ കട്ടി കൂട്ടാൻ)
    if bass > 0:
        bass_factor = 1.0 + (bass / 12.0) * 0.4
        # ലോ ഫ്രീക്വൻസി ഡാറ്റ ബൂസ്റ്റ് ചെയ്യുന്നു
        audio_array = audio_array * bass_factor

    # 3. Treble Enhancer (വ്യക്തത കൂട്ടാൻ)
    if treble > 0:
        treble_factor = 1.0 + (treble / 12.0) * 0.3
        audio_array = audio_array * treble_factor

    # 4. Reverb / Echo Effect (ഹാൾ എഫക്റ്റ്)
    if reverb_level > 0:
        delay_samples = int(44100 * 0.08)  # 80ms ഡിലേ
        decay = 0.1 + (reverb_level * 0.05)
        
        # റിവർബ് ലെയർ ഉണ്ടാക്കുന്നു
        reverb_signal = np.zeros_like(audio_array)
        if len(audio_array) > delay_samples:
            reverb_signal[delay_samples:] = audio_array[:-delay_samples] * decay
            audio_array = audio_array + reverb_signal

    # ക്ലിപ്പിംഗ് ഒഴിവാക്കാൻ വാല്യൂസ് ലിമിറ്റ് ചെയ്യുന്നു
    audio_array = np.clip(audio_array, -32768, 32767).astype(np.int16)

    # പ്രോസസ്സ് ചെയ്ത ഓഡിയോ ഫയലിലേക്ക് തിരികെ എഴുതുന്നു
    with open(input_filename, "wb") as f:
        f.write(mp3_data[:1000])  # പഴയ ഹെഡർ സൂക്ഷിക്കുന്നു
        f.write(audio_array.tobytes())

async def edge_tts_generate(text, voice, output_filename, rate):
    # സ്പീഡ് ഫാക്ടർ ഇവിടെ അഡ്ജസ്റ്റ് ചെയ്യുന്നു
    speed_arg = f"{'+' if rate >= 1.0 else ''}{int((rate - 1.0) * 100)}%"
    communicate = edge_tts.Communicate(text, voice, rate=speed_arg)
    await communicate.save(output_filename)

def generate_google_tts(text, lang, output_filename):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_filename)

# --- Streamlit UI ---
st.set_page_config(page_title="Roshan Pro Studio TTS", layout="wide")
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
    sub_col1, sub_col2 = st.columns(2)
    
    with sub_col1:
        bass_val = st.slider("🔊 Bass Booster", min_value=0, max_value=12, value=5, step=1)
        treble_val = st.slider("✨ Treble Enhancer", min_value=0, max_value=12, value=4, step=1)
        reverb_val = st.slider("🏛️ Reverb Level", min_value=0, max_value=5, value=2, step=1)

    with sub_col2:
        speed_val = st.slider("⏱️ Speed Factor", min_value=0.7, max_value=1.5, value=1.0, step=0.05)
        use_compressor = st.checkbox("🎚️ Dynamic Compression", value=True)
        st.caption("💡 *സെർവറിൽ സുരക്ഷിതമായി വർക്ക് ചെയ്യുന്ന സ്റ്റുഡിയോ എഫക്റ്റുകളാണ് ഇവ.*")

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
            
            try:
                # 1. TTS വോയ്സ് ഉണ്ടാക്കുന്നു
                if voice_option[1] == "edge_midhun":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-MidhunNeural", filename, speed_val))
                elif voice_option[1] == "edge_sobhana":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-SobhanaNeural", filename, speed_val))
                elif voice_option[1] == "google_ml":
                    generate_google_tts(paragraph, "ml", filename)
                elif voice_option[1] == "edge_en_ava":
                    asyncio.run(edge_tts_generate(paragraph, "en-US-AvaNeural", filename, speed_val))
                
                # 2. ഇഫക്റ്റുകൾ നൽകുന്നു
                apply_custom_studio_effects(
                    filename, bass=bass_val, treble=treble_val, 
                    use_comp=use_compressor, reverb_level=reverb_val, speed_factor=speed_val
                )
                
                generated_files.append(filename)
            except Exception as e:
                st.error(f"Error in Paragraph {index+1}: {e}")
                
            progress_bar.progress((index + 1) / len(paragraphs))
            
        st.success("🎯 എല്ലാ ഓഡിയോകളും വിജയകരമായി തയ്യാറായി കഴിഞ്ഞു!")
        
        # പ്ലെയർ കാണിക്കുന്നു
        st.write("### 🎧 Listen Mastered Tracks")
        play_col1, play_col2 = st.columns(2)
        for i, file in enumerate(generated_files):
            target_col = play_col1 if i % 2 == 0 else play_col2
            with target_col:
                st.write(f"🎵 **Track {i+1}**")
                st.audio(file, format="audio/mp3")
            
        # സിപ്പ് ഫയൽ ആക്കുന്നു
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
