import streamlit as st
from groq import Groq
import base64
from PIL import Image, ExifTags
import io
import hashlib
import urllib.parse
import requests

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")

# --- SAFE KEY CHECK - No crash ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Add GROQ_API_KEY in Streamlit > Settings > Secrets")
    st.stop()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def search_internet(query):
    try:
        # Try DuckDuckGo Instant Answer
        url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&pretty=1"
        r = requests.get(url, timeout=8)
        data = r.json()
        result = ""
        if data.get("AbstractText"):
            result += data["AbstractText"] + "\n"
        if data.get("RelatedTopics"):
            for t in data["RelatedTopics"][:2]:
                if isinstance(t, dict) and "Text" in t:
                    result += t["Text"] + "\n"

        if result.strip():
            return result[:2000]
        else:
            return "No live results, use your own knowledge."
    except Exception:
        return "No live results, use your own knowledge."

def compress(file):
    try:
        file.seek(0)
        img = Image.open(file)
        # Fix rotation
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation]=='Orientation':
                    break
            exif = img._getexif()
            if exif is not None:
                orient = exif.get(orientation)
                if orient == 3: img = img.rotate(180, expand=True)
                elif orient == 6: img = img.rotate(270, expand=True)
                elif orient == 8: img = img.rotate(90, expand=True)
        except: pass

        img.thumbnail((1024, 1024))
        if img.mode!="RGB":
            img = img.convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        return base64.b64encode(buf.getvalue()).decode()
    except Exception as e:
        st.error(f"Image process error: {e}")
        return None

def generate_image_url(prompt):
    clean_prompt = prompt.strip()
    encoded = urllib.parse.quote(clean_prompt)
    seed = hashlib.md5(clean_prompt.encode()).hexdigest()[:6]
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&model=flux&seed={seed}"

SYSTEM_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota from Abuja.
Your knowledge is always up to date. You are trained on everything on the internet.
You understand Nigeria Pidgin, all slangs, you know "fashi" means forget it, leave it.

RULES:
- NEVER give Unsplash links or any image links. NEVER say "go to Unsplash".
- If user asks for image, just say "I will generate it" - the system will handle it. Do not give links.
- For Maths: Formula, Substitute, Solve, give final answer. Use $F=ma$
- Be friendly, short answers.
- If Internet info is provided, use it to give current answers.
"""

st.title("🤖 Emmanuel AI")
st.caption("Your personal AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "last_voice_hash" not in st.session_state:
    st.session_state.last_voice_hash = None

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m:
            st.image(m["image_url"])

with st.sidebar:
    img_file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
    if img_file:
        st.image(img_file, width=200)

    # Safe audio input
    try:
        audio_file = st.audio_input("🎤 Voice")
    except:
        audio_file = None

    if st.button("Clear Chat"):
        st.session_state.msgs = []
        st.session_state.last_voice_hash = None
        st.rerun()

# --- FIXED VOICE LOGIC ---
voice_text = None
if audio_file is not None:
    audio_bytes = audio_file.getvalue()
    if len(audio_bytes) > 1000:
        h = hashlib.md5(audio_bytes).hexdigest()
        if h!= st.session_state.last_voice_hash:
            try:
                with st.spinner("Listening..."):
                    transcription = client.audio.transcriptions.create(
                        model="whisper-large-v3",
                        file=("voice.wav", audio_bytes),
                        response_format="text"
                    )
                    voice_text = transcription if isinstance(transcription, str) else transcription.text
                    st.session_state.last_voice_hash = h
                    if voice_text:
                        st.toast(f"You said: {voice_text}")
            except Exception as e:
                st.error(f"Voice error: {e}")

text_q = st.chat_input("Ask anything...")
final_query = voice_text if voice_text else text_q

if not final_query and img_file:
    final_query = "Explain this image step by step"

if final_query:
    lower_q = final_query.lower()
    gen_keywords = ["generate image", "create image", "draw", "make image", "generate a image", "create a picture", "generate picture", "create an image"]
    is_gen = any(k in lower_q for k in gen_keywords)

    st.session_state.msgs.append({"role":"user","content": final_query})
    with st.chat_message("user"):
        st.markdown(final_query)
        if img_file:
            st.image(img_file, width=300)

    with st.chat_message("assistant"):
        if is_gen:
            # Extract clean prompt
            prompt = final_query
            for k in ["can you", "please", "generate image", "create image", "generate a image", "make image", "draw image", "generate picture", "create picture", "of", "a image of", "an image of", "create an image", "generate an image"]:
                prompt = prompt.lower().replace(k, " ")
            prompt = " ".join(prompt.split()).strip()
            if not prompt or len(prompt) < 3:
                prompt = "beautiful landscape, highly detailed"

            st.markdown(f"🎨 Generating: **{prompt}**...")
            try:
                img_url = generate_image_url(prompt)
                st.image(img_url, caption=prompt)
                st.session_state.msgs.append({"role":"assistant","content": f"Here is your image: {prompt}", "image_url": img_url})
            except Exception as e:
                st.error(f"Image error: {e}")
        else:
            with st.spinner("Thinking..."):
                search_data = search_internet(final_query)
                if "No live results" in search_data:
                    st.caption("🔍 No live web result, answering from knowledge")
                else:
                    st.caption(f"🌐 Found live info: {search_data[:80]}...")

            history = [{"role":"system","content": SYSTEM_PROMPT}]
            if search_data and "No live results" not in search_data:
                history.append({"role":"system","content": f"Internet info: {search_data}"})

            # Fixed history slice
            for m in st.session_state.msgs[-8:]:
                if m["role"]!= "user" or m["content"]!= final_query:
                    history.append({"role": m["role"], "content": m["content"]})

            b64 = None
            if img_file:
                b64 = compress(img_file)

            if b64:
                history.append({"role":"user","content": [{"type":"text","text": final_query},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]})
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
            else:
                history.append({"role":"user","content": final_query})
                model = "openai/gpt-oss-20b"

            try:
                resp = client.chat.completions.create(model=model, messages=history, max_tokens=2000, temperature=0.3)
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.msgs.append({"role":"assistant","content": ans})
            except Exception as e:
                st.error(f"Error: {e}. Try again or clear chat.")
