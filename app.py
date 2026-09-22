import streamlit as st
from groq import Groq
import base64
from PIL import Image, ExifTags
import io
import hashlib
import urllib.parse
import requests
import random
import time

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")

if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY in Streamlit > Settings > Secrets")
    st.stop()

# Initialize API Client
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def search_internet(query):
    try:
        url = f"https://duckduckgo.com{urllib.parse.quote(query)}&format=json&pretty=1"
        r = requests.get(url, timeout=5)
        data = r.json()
        result = data.get("AbstractText", "")
        return result[:1500] if result else "No live results"
    except:
        return "No live results"

def compress(file):
    try:
        file.seek(0)
        img = Image.open(file)
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            exif = img._getexif()
            if exif:
                orient = exif.get(orientation)
                if orient == 3: img = img.rotate(180, expand=True)
                elif orient == 6: img = img.rotate(270, expand=True)
                elif orient == 8: img = img.rotate(90, expand=True)
        except: 
            pass
        img.thumbnail((1024, 1024))
        if img.mode != "RGB": 
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except: 
        return None

def generate_image_url(prompt, fallback_model=False):
    encoded = urllib.parse.quote(prompt.strip()[:400])
    seed = random.randint(1, 9999999)
    # Uses ultra-premium Flux by default, switches to Stable Diffusion 3 if fallback triggered
    model_choice = "sd3" if fallback_model else "flux"
    return f"https://pollinations.ai{encoded}?width=1024&height=1024&nologo=true&model={model_choice}&seed={seed}&enhance=true"

# Helper function for true typewriter streaming effect
def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.01)

SYSTEM_PROMPT = "You are Emmanuel AI by Emmanuel Ebhota from Abuja. Never give Unsplash links. Be friendly, short, understand Nigeria pidgin."

st.title("🤖 Emmanuel AI")
st.caption("Your multi-talented AI assistant built by Emmanuel Ebhota")

# Initialize Session States
if "msgs" not in st.session_state: 
    st.session_state.msgs = []
if "last_voice_hash" not in st.session_state: 
    st.session_state.last_voice_hash = None
if "last_image_prompt" not in st.session_state: 
    st.session_state.last_image_prompt = "beautiful landscape, highly detailed"

# Render Chat History cleanly
for idx, m in enumerate(st.session_state.msgs):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m: 
            st.image(m["image_url"], caption=m.get("prompt_caption", ""))
            # Download tool for historic images using unique button IDs
            try:
                img_data = requests.get(m["image_url"]).content
                st.download_button(label="📥 Download This Image", data=img_data, file_name=f"emmanuel_ai_{idx}.jpg", mime="image/jpeg", key=f"dl_{idx}")
            except:
                pass
        if "uploaded_img" in m and m["uploaded_img"]:
            st.image(m["uploaded_img"], width=250)

# Sidebar controls
with st.sidebar:
    st.markdown("### 🛠️ Multimedia Tools")
    img_file = st.file_uploader("Upload image for Emmanuel to look at", type=["jpg","jpeg","png"])
    if img_file: 
        st.image(img_file, width=200)
    
    try: 
        audio_file = st.audio_input("🎤 Speak to Emmanuel")
    except: 
        audio_file = None
        
    st.markdown("---")
    if st.button("🗑️ Clear Chat Records", use_container_width=True):
        st.session_state.msgs = []
        st.session_state.last_image_prompt = "beautiful landscape, highly detailed"
        st.session_state.last_voice_hash = None
        st.rerun()

# Process voice transcription pipeline
voice_text = None
if audio_file:
    b = audio_file.getvalue()
    if len(b) > 1000:
        h = hashlib.md5(b).hexdigest()
        if h != st.session_state.last_voice_hash:
            try:
                tr = client.audio.transcriptions.create(model="whisper-large-v3", file=("voice.wav", b), response_format="text")
                voice_text = tr if isinstance(tr, str) else tr.text
                st.session_state.last_voice_hash = h
                st.toast(f"🗣️ Transcribed: {voice_text}")
            except Exception as e: 
                st.error(f"Voice engine warning: {e}")

text_q = st.chat_input("Ask me anything or ask me to draw something...")
final_query = voice_text if voice_text else text_q

if final_query:
    lower = final_query.lower().strip()

    gen_keywords = ["generate image","create image","generate picture","create picture","draw","make image","generate","create an image","create a image"]
    regen_keywords = ["i dont like", "don't like", "dont like", "oya do", "do it", "another", "different", "change", "do am", "another one", "not this", "other", "new one", "fashi", "oya"]

    is_gen = any(k in lower for k in gen_keywords)
    is_regen = any(k in lower for k in regen_keywords)

    if is_regen and not is_gen:
        if st.session_state.last_image_prompt:
            is_gen = True
            final_query = st.session_state.last_image_prompt

    # CASE A: Upgraded Image Generation & Download Sequence
    if is_gen:
        prompt = final_query
        if is_regen:
            prompt = st.session_state.last_image_prompt
        else:
            temp = lower
            for k in ["can you","please","generate image","create image","make image","generate picture","create picture","generate an image","create an image","generate a image","create a image","generate","create","draw","an image of","a image of","image of","picture of","of"]:
                temp = temp.replace(k, " ")
            temp = " ".join(temp.split()).strip()
            prompt = temp if len(temp) >= 3 else st.session_state.last_image_prompt

        st.session_state.last_image_prompt = prompt
        st.session_state.msgs.append({"role": "user", "content": final_query})

        with st.chat_message("user"):
            st.markdown(final_query)

        with st.chat_message("assistant"):
            st.markdown(f"🎨 Drawing your vision: **{prompt}**...")
            
            # Primary Flux Attempt with automatic SD3 Fallback Core
            img_url = generate_image_url(prompt, fallback_model=False)
            try:
                response = requests.get(img_url, timeout=10)
                if response.status_code != 200:
                    raise Exception("Primary pipeline busy")
                img_data = response.content
            except:
                # Hot swap to Stable Diffusion 3 backup model instantly
                img_url = generate_image_url(prompt, fallback_model=True)
                img_data = requests.get(img_url).content
                
            st.image(img_url, caption=prompt)
            
            # Interactive direct local download utility
            st.download_button(label="📥 Download This Image", data=img_data, file_name="emmanuel_ai_art.jpg", mime="image/jpeg", key="dl_current")
            
            st.session_state.msgs.append({
                "role": "assistant", 
                "content": "Look at what I made for you! ✨", 
                "image_url": img_url,
                "prompt_caption": prompt
            })

    # CASE B: Real-Time Multimodal Text / Vision Engine Loop
    else:
        current_msg = {"role": "user", "content": final_query}
        if img_file:
            current_msg["uploaded_img"] = img_file
        st.session_state.msgs.append(current_msg)
        
        with st.chat_message("user"):
            st.markdown(final_query)
            if img_file: 
                st.image(img_file, width=250)

        with st.chat_message("assistant"):
            with st.spinner("Searching and thinking..."):
                search_data = search_internet(final_query)

            history = [{"role": "system", "content": SYSTEM_PROMPT}]
            if "No live results" not in search_data:
                history.append({"role": "system", "content": f"Web info: {search_data}"})
            
           
                  
                try:
