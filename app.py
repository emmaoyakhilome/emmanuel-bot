import streamlit as st
from groq import Groq
import base64
from PIL import Image, ExifTags
import io
import hashlib
import urllib.parse
import requests

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def search_internet(query):
    try:
        # Search DuckDuckGo + Wikipedia for every question
        result = ""
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&pretty=1"
            r = requests.get(url, timeout=8)
            data = r.json()
            if data.get("AbstractText"):
                result += data["AbstractText"] + "\n"
            if data.get("RelatedTopics"):
                for topic in data["RelatedTopics"][:3]:
                    if isinstance(topic, dict) and "Text" in topic:
                        result += topic["Text"] + "\n"
        except:
            pass

        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(query)}"
            w = requests.get(wiki_url, timeout=5)
            if w.status_code == 200:
                j = w.json()
                if j.get("extract"):
                    result += j["extract"] + "\n"
        except:
            pass

        return result[:2500] if result else "Use your own vast knowledge, search didn't return anything."
    except:
        return "Use your own vast knowledge."

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
    encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"

# --- THIS IS THE MAIN FIX YOU ASKED FOR ---
SYSTEM_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota.

YOUR KNOWLEDGE IS ALWAYS UP TO DATE.

You are trained on EVERYTHING on the internet and apart from only the internet, everything on the internet about any question asked. You search the internet for every question to give the most current and accurate answer.

You understand all Nigerian Pidgin, Yoruba slang, Igbo slang, Hausa, street slang, Gen Z slang worldwide. You know "fashi" means forget it, leave it.

HOW YOU ANSWER:
- You ALWAYS receive internet search results for every question. Use them to give up-to-date answer.
- Your knowledge is always up to date, you know everything on the internet and beyond.
- Be friendly like Meta AI.
- For Maths: Show Formula, Substitute, Solve, then give final answer normally. Use $F=ma$ latex.

You are Emmanuel AI - Your personal AI with always up to date knowledge from everything on the internet.
"""

st.title("🤖 Emmanuel AI")
st.caption("Your personal AI - Knowledge is always up to date")

if "msgs" not in st.session_state:
    st.session_state.msgs = []
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if "image_url" in m:
            st.image(m["image_url"])

with st.sidebar:
    img_file = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
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

text_q = st.chat_input("Ask anything - I search everything on internet")
final_query = voice_text if voice_text else text_q
if not final_query and img_file:
    final_query = "Solve this image"

if final_query:
    gen_keywords = ["generate image", "create image", "draw image", "make image"]
    is_gen = any(k in final_query.lower() for k in gen_keywords)

    st.session_state.msgs.append({"role":"user","content": final_query})
    with st.chat_message("user"):
        st.markdown(final_query)
        if img_file:
            st.image(img_file, width=300)

    with st.chat_message("assistant"):
        if is_gen:
            prompt = final_query.lower()
            for k in gen_keywords:
                prompt = prompt.replace(k, "")
            prompt = prompt.replace("of", "", 1).strip()
            if not prompt: prompt = "beautiful landscape"
            st.markdown(f"Generating **{prompt}**...")
            img_url = generate_image(prompt)
            st.image(img_url, caption=prompt)
            st.session_state.msgs.append({"role":"assistant","content": f"Generated: {prompt}", "image_url": img_url})
        else:
            # ALWAYS SEARCH INTERNET FOR EVERY QUESTION - THIS IS WHAT YOU ASKED
            with st.spinner("Searching everything on internet..."):
                search_result = search_internet(final_query)

            history = [{"role":"system","content": SYSTEM_PROMPT}]
            history.append({"role":"system","content": f"INTERNET SEARCH RESULTS FOR '{final_query}' (Your knowledge is always up to date, use this):\n{search_result}"})

            for m in st.session_state.msgs[-10:-1]:
                history.append({"role": m["role"], "content": m["content"]})

            if img_file:
                b64 = compress(img_file)
                history.append({"role":"user","content": [{"type":"text","text": final_query},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]})
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
            else:
                history.append({"role":"user","content": final_query})
                model = "openai/gpt-oss-20b"

            try:
                resp = client.chat.completions.create(model=model, messages=history, max_tokens=2500)
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.msgs.append({"role":"assistant","content": ans})
            except Exception as e:
                st.error(f"Error: {e}")
