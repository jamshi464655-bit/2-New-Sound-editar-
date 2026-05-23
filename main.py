import streamlit as st
import asyncio
import edge_tts
from gtts import gTTS
import os
import zipfile
from io import BytesIO

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
    st.write("### ℹ️ Web Server Status")
    st.info("🌐 Web Hosting Mode: സെർവറിൽ മികച്ച സ്പീഡിലും എറർ ഇല്ലാതെയും വർക്ക് ചെയ്യാൻ പാകത്തിലാണ് ഈ വേർഷൻ കോൺഫിഗർ ചെയ്തിരിക്കുന്നത്.")

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
            try:
                if voice_option[1] == "edge_midhun":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-MidhunNeural", filename))
                elif voice_option[1] == "edge_sobhana":
                    asyncio.run(edge_tts_generate(paragraph, "ml-IN-SobhanaNeural", filename))
                elif voice_option[1] == "google_ml":
                    generate_google_tts(paragraph, "ml", filename)
                elif voice_option[1] == "edge_en_ava":
                    asyncio.run(edge_tts_generate(paragraph, "en-US-AvaNeural", filename))
                
                generated_files.append(filename)
            except Exception as e:
                st.error(f"Error in Paragraph {index+1}: {e}")
                
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
