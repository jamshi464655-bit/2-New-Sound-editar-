import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
import os
import zipfile
from io import BytesIO
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range, normalize

# --- WEB CLOUD FFMPEG CONFIGURATION ---
# സ്ട്രീംലിറ്റ് ക്ലൗഡ് സെർവറിലെ FFmpeg പാത്ത് ലിങ്ക് ചെയ്യുന്നു (Error ഒഴിവാക്കാൻ)
AudioSegment.converter = "/usr/bin/ffmpeg"
AudioSegment.ffprobe = "/usr/bin/ffprobe"

# --- ഓഡിയോ പ്രോസസ്സിംഗ് ഫങ്ക്ഷൻ ---
def apply_advanced_studio_effects(input_filename, bass, treble, use_comp, reverb_level, speed_factor, vocal_boost):
    # ഓഡിയോ ഫയൽ ലോഡ് ചെയ്യുന്നു
    audio = AudioSegment.from_file(input_filename)
    audio = normalize(audio)
    
    # വോക്കൽ ബൂസ്റ്റർ (Vocal Presence)
    if vocal_boost:
        vocal_range = audio.filter_bank_highpass(300).filter_bank_lowpass(3000).apply_gain(3)
        audio = audio.overlay(vocal_range)

    # ബാസ്സ് ബൂസ്റ്റർ (Bass Booster)
    if bass > 0:
        bass_part = audio.low_pass_filter(150).apply_gain(bass)
        audio = audio.overlay(bass_part)
        
    # ട്രബിൾ എൻഹാൻസർ (Treble Enhancer)
    if treble > 0:
        treble_part = audio.high_pass_filter(2500).apply_gain(treble)
        audio = audio.overlay(treble_part)

    # ട്രൂ റിവർബ് (True Reverb)
    if reverb_level > 0:
        reverb_layer = audio.apply_gain(-12 + reverb_level)
        audio = audio.overlay(reverb_layer, position=5)
        audio = audio.overlay(reverb_layer, position=10)

    # ഡൈനാമിക് കംപ്രസ്സർ (Dynamic Compression)
    if use_comp:
        audio = compress_dynamic_range(audio, threshold=-18.0, ratio=3.5, attack=10.0, release=60.0)

    # സ്പീഡ് കൺട്രോൾ (Speed / Pitch Factor)
    if speed_factor != 1.0:
        new_sample_rate = int(audio.frame_rate * speed_factor)
        audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
        audio = audio.set_frame_rate(44100)

    # ഹൈ-ക്വാളിറ്റിയിൽ എക്സ്പോർട്ട് ചെയ്യുന്നു
    audio.export(input_filename, format="mp3", bitrate="192k")

async def edge_tts_generate(text, voice, output_filename):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_filename)

def generate_google_tts(text, lang, output_filename):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save(output_filename)

# --- Streamlit UI ---
st.set_page_config(page_title="Pro Studio TTS - Cloud", layout="wide")
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
        bass_val = st.slider("🔊 Bass Booster (dB)", min_value=0, max_value=12, value=5, step=1)
        treble_val = st.slider("✨ Treble Enhancer", min_value=0, max_value=12, value=4, step=1)
        reverb_val = st.slider("🏛️ True Reverb Level", min_value=0, max_value=5, value=2, step=1)

    with sub_col2:
        speed_val = st.slider("⏱️ Speed / Pitch Factor", min_value=0.7, max_value=1.5, value=1.0, step=0.05)
        use_compressor = st.checkbox("🎚️ Dynamic Compression", value=True)
        vocal_boost_val = st.checkbox("🗣️ Vocal Presence Booster", value=True)

st.write("---")

if st.button("🚀 Process & Generate Studio Audio", type="primary", use_container_width=True):
    if not text_input.strip():
        st.warning("ദയവായി ടെക്സ്റ്റ് ബോക്സിൽ എന്തെങ്കിലും ടെക്സ്റ്റ് നൽകുക.")
    else:
        # പാരഗ്രാഫുകളായി തിരിക്കുന്നു
        paragraphs = [p.strip() for p in text_input.split("\n") if p.strip()]
        st.info(f"📋 ആകെ {len(paragraphs)} പാരഗ്രാഫുകൾ കണ്ടെത്തി. പ്രൊസസ്സിംഗ് ആരംഭിക്കുന്നു...")
        
        generated_files = []
        progress_bar = st.progress(0)
        
        for index, paragraph in enumerate(paragraphs):
            filename = f"studio_paragraph_{index + 1}.mp3"
            
            # വോയ്‌സ് ജനറേഷൻ
            if voice_option[1] == "edge_midhun":
                asyncio.run(edge_tts_generate(paragraph, "ml-IN-MidhunNeural", filename))
            elif voice_option[1] == "edge_sobhana":
                asyncio.run(edge_tts_generate(paragraph, "ml-IN-SobhanaNeural", filename))
            elif voice_option[1] == "google_ml":
                generate_google_tts(paragraph, "ml", filename)
            elif voice_option[1] == "edge_en_ava":
                asyncio.run(edge_tts_generate(paragraph, "en-US-AvaNeural", filename))
                
            # ഓഡിയോ എഫക്റ്റുകൾ നൽകുന്നു
            try:
                apply_advanced_studio_effects(
                    filename, bass=bass_val, treble=treble_val, 
                    use_comp=use_compressor, reverb_level=reverb_val, 
                    speed_factor=speed_val, vocal_boost=vocal_boost_val
                )
            except Exception as e:
                st.error(f"എഫക്റ്റ് പ്രോസസ്സ് ചെയ്തപ്പോൾ ഒരു തകരാർ (Paragraph {index+1}): {e}")
                
            generated_files.append(filename)
            progress_bar.progress((index + 1) / len(paragraphs))
            
        st.success("🎯 എല്ലാ ഓഡിയോകളും വിജയകരമായി തയ്യാറായി കഴിഞ്ഞു!")
        
        # പ്ലെയർ ഡിസ്‌പ്ലേ
        st.write("### 🎧 Listen Mastered Tracks")
        play_col1, play_col2 = st.columns(2)
        for i, file in enumerate(generated_files):
            target_col = play_col1 if i % 2 == 0 else play_col2
            with target_col:
                st.write(f"🎵 **Track {i+1}**")
                st.audio(file, format="audio/mp3")
            
        # സിപ്പ് ഫയൽ നിർമ്മാണം
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file in generated_files:
                zip_file.write(file)
                os.remove(file) # സെർവർ മെമ്മറി ക്ലിയർ ചെയ്യാൻ ഫയൽ ഡിലീറ്റ് ചെയ്യുന്നു
                
        st.write("---")
        st.download_button(
            label="📦 Download All Mastered Audios (ZIP)",
            data=zip_buffer.getvalue(),
            file_name="roshan_studio_outputs.zip",
            mime="application/zip",
            use_container_width=True
        )