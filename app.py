import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress_image(file):
    img = Image.open(file)
    img.thumbnail((512, 512)) # smaller now
    if img.mode in ("RGBA","P","LA"):
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    return buf.getvalue()

SYSTEM_PROMPT = "You are Emmanuel AI by Emmanuel Ebhota. Search internet first. Friendly. Never romantic."

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    uploaded = st.file_uploader("📷 Upload image (optional)", type=["jpg","jpeg","png"], accept_multiple_files=False)
    use_image = st.checkbox("✅ Attach image to next question", value=False, help="Only tick this when you want to ask about the image. Leave unticked for normal text chat like Japanese translations")
    if uploaded:
        st.image(uploaded, width=200)
        st.caption(f"Size: {len(uploaded.getvalue())/1024:.1f} KB")

user_input = st.chat_input("Ask anything...")
audio = st.audio_input("🎤")

user_text = user_input
if audio and not user_text:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio.name, audio.getvalue()),
            model="whisper-large-v3-turbo", response_format="text"
        )
        user_text = trans
    except Exception as e:
        st.error(f"Audio: {e}")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("..."):
            try:
                # TEXT ONLY by default - NO 413
                if uploaded and use_image:
                    comp = compress_image(uploaded)
                    b64 = base64.b64encode(comp).decode()
                    content = [
                        {"type":"text","text": user_text},
                        {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                    ]
                    resp = client.chat.completions.create(
                        model="meta-llama/llama-4-maverick-17b-128e-instruct",
                        messages=[{"role":"user","content":content}],
                        max_tokens=800
                    )
                else:
                    # PURE TEXT - will never give 413
                    resp = client.chat.completions.create(
                        model="groq/compound",
                        messages=[{"role":"system","content": SYSTEM_PROMPT},{"role":"user","content": user_text}],
                        max_tokens=1000
                    )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")
