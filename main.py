import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
import os
import zipfile
from io import BytesIO
from pedalboard import Pedalboard, Compressor, HighpassFilter, LowpassFilter, PeakFilter, Reverb
import io
import soundfile as sf

# --- അഡ്വാൻസ്ഡ് സ്റ്റുഡിയോ എഫക്റ്റ് ഫങ്ക്ഷൻ (Using Pedalboard) ---
def apply_advanced_studio_effects(input_filename, bass, treble, use_comp, reverb_level, speed_factor):
    # ഓഡിയോ ഫയൽ റീഡ് ചെയ്യുന്നു
    data, samplerate = sf.read(input_filename)
    
    # സ്റ്റീരിയോ ഫയലുകളെ മോണോ ആക്കുന്നു (പ്രോസസ്സിംഗ് എളുപ്പമാക്കാൻ)
    if len(data.shape) > 1:
        data = data[:, 0]

    # പെഡൽബോർഡ് ബോക്സ് സെറ്റ് ചെയ്യുന്നു
    board_effects = []

    # 1. Dynamic Compressor
    if use_comp:
        board_effects.append(Compressor(threshold_db=-16, ratio=3.5, attack_ms=10, release_ms=60))

    # 2. Bass Booster (Low Shelf / Peak Filter around 100Hz)
    if bass > 0:
        board_effects.append(PeakFilter(cutoff_frequency_hz=100, gain_db=bass, q=1.0))

    # 3. Treble Enhancer (High Pass / Peak Filter around 3000Hz)
    if treble > 0:
        board_effects.append(PeakFilter(cutoff_frequency_hz=3500, gain_db=treble, q=1.0))

    # 4. True Reverb (ഹാൾ എഫക്റ്റ്)
    if reverb_level > 0:
        # റൂം സൈസ് റിവർബ് ലെവലിനനുസരിച്ച് മാറ്റുന്നു
        room_size = 0.3 + (reverb_level * 0.1)
        board_effects.append(Reverb(room_size=room_size, wet_level=0.15, dry_level=0.85))

    # എഫക്റ്റുകൾ ഓഡിയോയിലേക്ക് അപ്ലൈ ചെയ്യുന്നു
    board = Pedalboard(board_effects)
    effected_data = board(data, samplerate)

    # 5. Speed Factor (വേഗത മാറ്റാൻ)
    if speed_factor != 1.0:
        samplerate = int(samplerate * speed_factor)

    # മാസ്റ്റേഡ് ഓഡിയോ തിരികെ ഫയലിലേക്ക് സേവ് ചെയ്യുന്നു
    sf.write(input_filename, effected_data, samplerate, format='MP3', bitrate='192k')

async def edge_tts_generate(text, voice, output_filename):
    communicate = edge_tts.Communicate(text, voice)
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
        bass_val = st.slider("🔊 Bass Booster (dB)", min_value=0, max_value=12, value=6, step=1)
        treble_val = st.slider("✨ Treble Enhancer (dB)", min_value=0, max_value=12, value=5, step=1)
        reverb_val = st.slider("🏛️ True Reverb Level", min_value=0, max_value=5, value=2, step=1)

    with sub_col2:
        speed_val = st.slider("⏱️ Speed Factor", min_value=0.7, max_value=1.5, value=1.0, step=0.05)
        use_compressor = st.checkbox("🎚️ Dynamic Compression", value=True)
        st.caption("💡 *Compression ഓൺ ചെയ്താൽ ശബ്ദം ഒരേ ലെവലിൽ നിലനിൽക്കും.*")

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
            
            # 1. TTS ജനറേഷൻ
            try:
                if voice_option[1] == "edge_midhun":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-MidhunNeural", filename))
                elif voice_option[1] == "edge_sobhana":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-SobhanaNeural", filename))
                elif voice_option[1] == "google_ml":
                    generate_google_tts(paragraph, "ml", filename)
                elif voice_option[1] == "edge_en_ava":
                    asyncio.run(edge_tts_generate(paragraph, "en-US-AvaNeural", filename))
                
                # 2. പെഡൽബോർഡ് സ്റ്റുഡിയോ എഫക്റ്റുകൾ നൽകുന്നു
                apply_advanced_studio_effects(
                    filename, bass=bass_val, treble=treble_val, 
                    use_comp=use_compressor, reverb_level=reverb_val, speed_factor=speed_val
                )
                
                generated_files.append(filename)
            except Exception as e:
                st.error(f"Error in Paragraph {index+1}: {e}")
                
            progress_bar.progress((index + 1) / len(paragraphs))
            
        st.success("🎯 എല്ലാ ഓഡിയോകളും സ്റ്റുഡിയോ ക്വാളിറ്റിയിൽ തയ്യാറായി കഴിഞ്ഞു!")
        
        # ഓഡിയോ പ്ലെയർ ഡിസ്‌പ്ലേ
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
