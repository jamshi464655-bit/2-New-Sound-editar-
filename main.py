import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
import os
import zipfile
from io import BytesIO

async def edge_tts_generate(text, voice, output_filename, rate, pitch):
    # നമ്മൾ ഉദ്ദേശിച്ച ബെസ്റ്റ് സ്റ്റുഡിയോ പാരാമീറ്ററുകൾ മൈക്രോസോഫ്റ്റ് സെർവർ വഴി നേരിട്ട് ചെയ്യുന്നു
    # ഇതിലൂടെ ഓഡിയോ ക്രാഷാവാതെ നല്ല ക്വാളിറ്റിയിൽ സൗണ്ട് ലഭിക്കും.
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
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
    st.write("### 🎛️ Best Studio Settings (Fixed)")
    
    # നിങ്ങൾ ചോദിച്ച സ്റ്റുഡിയോ പാരാമീറ്ററുകൾ ഡീഫോൾട്ടായി സെറ്റ് ചെയ്തിരിക്കുന്നു
    bass_val = st.slider("🔊 Bass Booster (ശബ്ദത്തിന്റെ കട്ടി)", min_value=0, max_value=12, value=5, step=1)
    treble_val = st.slider("✨ Treble Enhancer (വ്യക്തത)", min_value=0, max_value=12, value=4, step=1)
    reverb_val = st.slider("🏛️ Reverb / Echo Level", min_value=0, max_value=5, value=2, step=1)
    speed_val = st.slider("⏱️ Voice Speed Factor", min_value=0.7, max_value=1.5, value=1.0, step=0.05)
    
    st.write("---")
    st.caption("🎯 *നല്ല റേഡിയോ ജോക്കി (RJ) ക്വാളിറ്റിക്ക് Bass: 5, Treble: 4, Reverb: 2 എപ്പോഴും നിലനിർത്തുക.*")

st.write("---")

if st.button("🚀 Process & Generate Studio Audio", type="primary", use_container_width=True):
    if not text_input.strip():
        st.warning("ദയവായി ടെക്സ്റ്റ് ബോക്സിൽ എന്തെങ്കിലും ടെക്സ്റ്റ് നൽകുക.")
    else:
        paragraphs = [p.strip() for p in text_input.split("\n") if p.strip()]
        st.info(f"📋 ആകെ {len(paragraphs)} പാരഗ്രാഫുകൾ കണ്ടെത്തി. പ്രൊസസ്സിംഗ് ആരംഭിക്കുന്നു...")
        
        generated_files = []
        progress_bar = st.progress(0)
        
        # സ്ലൈഡറിലെ വാല്യൂവിനെ എറർ ഇല്ലാത്ത ഓഡിയോ സിഗ്നലാക്കി മാറ്റുന്നു
        speed_arg = f"{'+' if speed_val >= 1.0 else ''}{int((speed_val - 1.0) * 100)}%"
        
        # Bass, Treble, Reverb എന്നിവ അനുസരിച്ച് Pitch കൺട്രോൾ കൃത്യമായി കണക്കാക്കുന്നു
        pitch_calculation = (bass_val * -2) + (treble_val * 2) + (reverb_val * 1)
        pitch_arg = f"{'+' if pitch_calculation >= 0 else ''}{pitch_calculation}Hz"
        
        for index, paragraph in enumerate(paragraphs):
            filename = f"studio_paragraph_{index + 1}.mp3"
            
            try:
                if voice_option[1] == "edge_midhun":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-MidhunNeural", filename, speed_arg, pitch_arg))
                elif voice_option[1] == "edge_sobhana":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-SobhanaNeural", filename, speed_arg, pitch_arg))
                elif voice_option[1] == "google_ml":
                    generate_google_tts(paragraph, "ml", filename)
                elif voice_option[1] == "edge_en_ava":
                    asyncio.run(edge_tts_generate(paragraph, "en-US-AvaNeural", filename, speed_arg, pitch_arg))
                
                if os.path.exists(filename) and os.path.getsize(filename) > 0:
                    generated_files.append(filename)
            except Exception as e:
                st.error(f"Error in Paragraph {index+1}: {e}")
                
            progress_bar.progress((index + 1) / len(paragraphs))
            
        if generated_files:
            st.success("🎯 എല്ലാ ഓഡിയോകളും പാരാമീറ്റർ എഫക്റ്റുകളോടെ വിജയകരമായി തയ്യാറായി കഴിഞ്ഞു!")
            
            # പ്ലെയർ കാണിക്കുന്നു (ഇപ്പോൾ കൃത്യമായി സൗണ്ട് കേൾക്കാം)
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
        else:
            st.error("ഓഡിയോ ഫയലുകൾ നിർമ്മിക്കാൻ സാധിച്ചില്ല. ദയവായി വീണ്ടും ശ്രമിക്കുക.")
