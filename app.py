import streamlit as st
from groq import Groq
import base64
from PIL import Image, ExifTags
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(file):
    img = Image.open(file)
    try:
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        exif = img._getexif()
        if exif is not None:
            orient = exif.get(orientation)
            if orient == 3:
                img = img.rotate(180, expand=True)
            elif orient == 6:
                img = img.rotate(270, expand=True)
            elif orient == 8:
                img = img.rotate(90, expand=True)
    except:
        pass
    img.thumbnail((1024, 1024))
    if img.mode!="RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=65)
    return base64.b64encode(buf.getvalue()).decode()

SYSTEM_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota, created September 2026.
You have latest knowledge up to September 2026.
Solve step-by-step: Formula, Substitute, Solve, Box answer.
Use $F=ma$ style LaTeX. No \\mathbf. Use $$ for big equations.
If image uploaded, solve it.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "last_audio_id" not in st.session_state:
    st.session_state.last_audio_id = None

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    img_file = st.file_uploader("Upload question", type=["jpg","jpeg","png"])
    if img_file:
        st.image(img_file, width=200)
    audio_file = st.audio_input("🎤 Tap to speak")
    if st.button("Clear Chat"):
        st.session_state.msgs = []
        st.session_state.last_audio_id = None
        st.rerun()

voice_text = None
if audio_file and audio_file.id!= st.session_state.last_audio_id:
    with st.spinner("Transcribing..."):
        try:
            tr = client.audio.transcriptions.create(model="whisper-large-v3", file=(audio_file.name, audio_file.getvalue()))
            voice_text = tr.text
            st.session_state.last_audio_id = audio_file.id
            st.success(f"You said: {voice_text}")
        except Exception as e:
            st.error(f"Voice error: {e}")

text_q = st.chat_input("Ask anything")
final_query = voice_text if voice_text else text_q
if not final_query and img_file:
    final_query = "Solve the question in this image"

if final_query:
    st.session_state.msgs.append({"role":"user","content": final_query})
    with st.chat_message("user"):
        st.markdown(final_query)
        if img_file:
            st.image(img_file, width=250)

    with st.chat_message("assistant"):
        try:
            history = [{"role":"system","content": SYSTEM_PROMPT}]
            for h in st.session_state.msgs[:-1]:
                history.append({"role": h["role"], "content": h["content"]})

            if img_file:
                b64 = compress(img_file)
                history.append({"role":"user","content": [{"type":"text","text": final_query},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]})
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
            else:
                history.append({"role":"user","content": final_query})
                model = "openai/gpt-oss-20b"

            resp = client.chat.completions.create(model=model, messages=history, max_tokens=2500)
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content": ans})
        except Exception as e:
            st.error(f"Error: {e}")
