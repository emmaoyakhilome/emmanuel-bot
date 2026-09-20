import streamlit as st
from groq import Groq
import base64
from PIL import Image, ExifTags
import io
import hashlib
import urllib.parse
import requests
import random

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")

if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY in Streamlit > Settings > Secrets")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def search_internet(query):
    try:
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&pretty=1"
        r = requests.get(url, timeout=8)
        data = r.json()
        result = data.get("AbstractText","")
        return result[:1500] if result else "No live results"
    except:
        return "No live results"

def compress(file):
    try:
        file.seek(0)
        img = Image.open(file)
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation':
                    break
            exif = img._getexif()
            if exif:
                orient = exif.get(orientation)
                if orient == 3: img = img.rotate(180, expand=True)
                elif orient == 6: img = img.rotate(270, expand=True)
                elif orient == 8: img = img.rotate(90, expand=True)
        except: pass
        img.thumbnail((1024, 1024))
        if img.mode!="RGB": img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except: return None

def generate_image_url(prompt):
    encoded = urllib.parse.quote(prompt.strip()[:400])
    seed = random.randint(1, 9999999)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux&seed={seed}&enhance=true"

SYSTEM_PROMPT = "You are Emmanuel AI by Emmanuel Ebhota from Abuja. Never give Unsplash links. Be friendly, short, understand Nigeria pidgin."

st.title("🤖 Emmanuel AI")
st.caption("Your personal AI")

if "msgs" not in st.session_state: st.session_state.msgs = []
if "last_voice_hash" not in st.session_state: st.session_state.last_voice_hash = None
if "last_image_prompt" not in st.session_state: st.session_state.last_image_prompt = "beautiful landscape, highly detailed"

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m: st.image(m["image_url"])

with st.sidebar:
    img_file = st.file_uploader("Upload image to explain", type=["jpg","jpeg","png"])
    if img_file: st.image(img_file, width=200)
    try: audio_file = st.audio_input("🎤 Voice")
    except: audio_file = None
    if st.button("Clear Chat"):
        st.session_state.msgs = []
        st.session_state.last_image_prompt = "beautiful landscape, highly detailed"
        st.rerun()

voice_text = None
if audio_file:
    b = audio_file.getvalue()
    if len(b) > 1000:
        h = hashlib.md5(b).hexdigest()
        if h!= st.session_state.last_voice_hash:
            try:
                tr = client.audio.transcriptions.create(model="whisper-large-v3", file=("voice.wav", b), response_format="text")
                voice_text = tr if isinstance(tr, str) else tr.text
                st.session_state.last_voice_hash = h
                st.toast(f"You said: {voice_text}")
            except Exception as e: st.error(f"Voice error: {e}")

text_q = st.chat_input("Ask anything...")
final_query = voice_text if voice_text else text_q

if final_query:
    lower = final_query.lower().strip()

    gen_keywords = ["generate image","create image","generate picture","create picture","draw","make image","generate","create an image","create a image"]
    regen_keywords = ["i dont like", "don't like", "dont like", "oya do", "do it", "another", "different", "change", "do am", "another one", "not this", "other", "new one", "fashi", "oya"]

    is_gen = any(k in lower for k in gen_keywords)
    is_regen = any(k in lower for k in regen_keywords)

    # If user says "oya do it" after an image, treat as regen
    if is_regen and not is_gen:
        if st.session_state.last_image_prompt:
            is_gen = True
            final_query = st.session_state.last_image_prompt

    if is_gen:
        prompt = final_query
        if is_regen:
            prompt = st.session_state.last_image_prompt
        else:
            temp = lower
            for k in ["can you","please","generate image","create image","make image","generate picture","create picture","generate an image","create an image","generate a image","create a image","generate","create","draw","an image of","a image of","image of","picture of","of"]:
                temp = temp.replace(k, " ")
            temp = " ".join(temp.split()).strip()
            if len(temp) >= 3:
                prompt = temp
            else:
                prompt = st.session_state.last_image_prompt

        st.session_state.last_image_prompt = prompt
        st.session_state.msgs.append({"role":"user","content": final_query})

        with st.chat_message("user"):
            st.markdown(final_query)

        with st.chat_message("assistant"):
            st.markdown(f"🎨 Generating: **{prompt}**...")
            img_url = generate_image_url(prompt)
            st.image(img_url, caption=prompt)
            st.session_state.msgs.append({"role":"assistant","content": f"Here is your image: {prompt}", "image_url": img_url})

    else:
        st.session_state.msgs.append({"role":"user","content": final_query})
        with st.chat_message("user"):
            st.markdown(final_query)
            if img_file: st.image(img_file, width=250)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                search_data = search_internet(final_query)

            history = [{"role":"system","content": SYSTEM_PROMPT}]
            if "No live results" not in search_data:
                history.append({"role":"system","content": f"Web info: {search_data}"})
            for m in st.session_state.msgs[-6:]:
                if m["content"]!= final_query:
                    history.append({"role": m["role"], "content": m["content"]})

            b64 = compress(img_file) if img_file else None

            if b64:
                history.append({"role":"user","content": [{"type":"text","text": final_query},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]})
                # auto fallback vision models
                for vm in ["llama-3.2-11b-vision-preview","llama-3.2-90b-vision-preview","meta-llama/llama-4-scout-17b-16e-instruct"]:
                    try:
                        resp = client.chat.completions.create(model=vm, messages=history, max_tokens=1500)
                        ans = resp.choices[0].message.content
                        st.markdown(ans)
                        st.session_state.msgs.append({"role":"assistant","content": ans})
                        break
                    except Exception as e:
                        if vm == "meta-llama/llama-4-scout-17b-16e-instruct":
                            st.error(f"Vision error: {e}")
                        continue
            else:
                history.append({"role":"user","content": final_query})
                try:
                    resp = client.chat.completions.create(model="openai/gpt-oss-20b", messages=history, max_tokens=1500)
                    ans = resp.choices[0].message.content
                except:
                    resp = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=history, max_tokens=1500)
                    ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.msgs.append({"role":"assistant","content": ans})
