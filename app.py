import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress_image(file, max_size=800):
    img = Image.open(file)
    img.thumbnail((max_size, max_size))
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=65)
    return buf.getvalue()

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota in Abuja.
1. ALWAYS SEARCH INTERNET FIRST for facts using groq/compound.
2. Mirror user tone, friendly phone chat.
3. NEVER romantic roleplay.
4. Keep short for mobile.
"""

st.title("🤖 Emmanuel AI")
st.caption("Final - No 413 error")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    st.markdown("📷 Image (optional - clear after use)")
    uploaded = st.file_uploader("Upload", type=["jpg","jpeg","png"], label_visibility="collapsed", accept_multiple_files=False)
    if uploaded:
        st.image(uploaded, width=200)
        if st.button("Clear image"):
            uploaded = None
            st.rerun()

user_input = st.chat_input("Ask anything...")
audio = st.audio_input("🎤")

user_text = user_input
if audio and not user_text:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio.name, audio.getvalue()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )
        user_text = trans
    except Exception as e:
        st.error(f"Audio: {e}")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # IF IMAGE UPLOADED -> USE MAVERICK (meta-la) - NOT AFFECTED, WORKING
                if uploaded:
                    comp = compress_image(uploaded)
                    b64 = base64.b64encode(comp).decode()
                    content = [
                        {"type":"text","text": f"Describe image and answer: {user_text}"},
                        {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                    ]
                    resp = client.chat.completions.create(
                        model="meta-llama/llama-4-maverick-17b-128e-instruct", # <-- THIS IS YOUR meta-la, WORKING
                        messages=[{"role":"user","content":content}],
                        max_tokens=800
                    )
                    ans = resp.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role":"assistant","content":ans})
                else:
                    # TEXT ONLY - NO IMAGE, NO 413
                    resp = client.chat.completions.create(
                        model="groq/compound", # searches internet first
                        messages=[
                            {"role":"system","content": SYSTEM_PROMPT},
                            {"role":"user","content": user_text}
                        ],
                        max_tokens=1000
                    )
                    ans = resp.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role":"assistant","content":ans})

            except Exception as e:
                err = str(e)
                if "413" in err or "too_large" in err:
                    st.error("Image too big. I compressed it but still big. Clear image in sidebar and ask text again.")
                elif "404" in err or "not_found" in err:
                    # Fallback
                    resp2 = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[{"role":"system","content": SYSTEM_PROMPT},{"role":"user","content": user_text}],
                        max_tokens=1000
                    )
                    st.markdown(resp2.choices[0].message.content)
                else:
                    st.error(f"Error: {e}")
