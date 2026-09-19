import streamlit as st
from groq import Groq
import base64
from PIL import Image, ExifTags
import io
import hashlib
import requests
import urllib.parse

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(file):
    file.seek(0)
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

def generate_image(prompt):
    # Free image generator - no API key needed
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
    return url

SYSTEM_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota, created September 2026.
You have knowledge about everything and always up to date.
You are a personal ai.

RULES:
- Solve Maths step-by-step: Formula, Substitute, Solve, Box answer. Use $F=ma$.
- If user asks to generate/draw/create image, just say: "Generating image of [prompt]..." - don't try to describe it.
- Keep answers short for mobile.
- Remember all previous chat.
"""

st.title("🤖 Emmanuel AI")
st.caption("Your personal ai")

if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

# Show history
for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m:
            st.image(m["image_url"])

with st.sidebar:
    st.markdown("### 📷 & 🎙️")
    img_file = st.file_uploader("Upload question image", type=["jpg","jpeg","png"])
    if img_file:
        st.image(img_file, width=200)
    audio_file = st.audio_input("🎤 Tap to speak")
    if st.button("Clear Chat"):
        st.session_state.msgs = []
        st.session_state.last_hash = None
        st.rerun()

voice_text = None
if audio_file is not None:
    audio_bytes = audio_file.getvalue()
    h = hashlib.md5(audio_bytes).hexdigest()
    if h!= st.session_state.last_hash:
        with st.spinner("Listening..."):
            try:
                # THIS IS THE FIX FOR VOICE ERROR
                tr = client.audio.transcriptions.create(
                    model="whisper-large-v3-turbo",
                    file=("voice.wav", audio_bytes, "audio/wav"),
                    response_format="text"
                )
                voice_text = tr if isinstance(tr, str) else tr.text
                st.session_state.last_hash = h
                st.success(f"You said: {voice_text}")
            except Exception as e:
                st.error(f"Voice error: {e}")

text_q = st.chat_input("Ask anything, send image, or say 'generate image of...'")
final_query = voice_text if voice_text else text_q

# Auto prompt if only image
if not final_query and img_file:
    final_query = "Solve the question in this image step-by-step"

if final_query:
    # Check if user wants to GENERATE image
    gen_keywords = ["generate image", "create image", "draw image", "make image", "generate a image"]
    is_gen = any(k in final_query.lower() for k in gen_keywords)

    st.session_state.msgs.append({"role":"user","content": final_query})
    with st.chat_message("user"):
        st.markdown(final_query)
        if img_file:
            st.image(img_file, width=300)

    with st.chat_message("assistant"):
        if is_gen:
            # IMAGE GENERATION MODE
            try:
                prompt = final_query.lower()
                for k in gen_keywords:
                    prompt = prompt.replace(k, "")
                prompt = prompt.replace("of", "", 1).strip()
                if not prompt:
                    prompt = "a beautiful landscape"
                st.markdown(f"Generating image of **{prompt}**...")
                img_url = generate_image(prompt)
                st.image(img_url, caption=prompt)
                st.session_state.msgs.append({"role":"assistant","content": f"Generated image of: {prompt}", "image_url": img_url})
            except Exception as e:
                st.error(f"Image gen error: {e}")
        else:
            # NORMAL CHAT + VISION MODE WITH MEMORY
            try:
                history = [{"role":"system","content": SYSTEM_PROMPT}]
                # Add memory - last 10 messages only to avoid token limit
                for m in st.session_state.msgs[-10:-1]:
                    history.append({"role": m["role"], "content": m["content"]})

                if img_file:
                    b64 = compress(img_file)
                    history.append({
                        "role":"user",
                        "content": [
                            {"type":"text","text": final_query},
                            {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                        ]
                    })
                    model = "meta-llama/llama-4-scout-17b-16e-instruct"
                else:
                    history.append({"role":"user","content": final_query})
                    model = "openai/gpt-oss-20b"

                resp = client.chat.completions.create(
                    model=model,
                    messages=history,
                    max_tokens=2000
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.msgs.append({"role":"assistant","content": ans})
            except Exception as e:
                st.error(f"Error: {e} - Try again")
