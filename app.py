import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(file):
    img = Image.open(file)
    # Fix rotation
    try:
        from PIL import ExifTags
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
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=65)
    return base64.b64encode(buf.getvalue()).decode()

SYSTEM_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota - A smart assistant like Meta AI.

CORE RULES:
- Solve Maths/Physics/Chemistry step-by-step: 1. Formula 2. Substitute 3. Solve 4. Box answer.
- Use CLEAN LaTeX: $F=ma$, $W=Fd$, $K=\\frac{1}{2}mv^2$, $U=mgh$. NEVER use \\mathbf.
- Use $$ for big equations. End with \\boxed{answer}.
- If image is uploaded: read the question in the image carefully and solve it.
- If translation asked: give accurate translation + meaning + example.
- Be friendly, smart, helpful. Keep short for mobile.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    st.markdown("### 📷 & 🎙️")
    img_file = st.file_uploader("Upload question image", type=["jpg","jpeg","png"])
    if img_file:
        st.image(img_file, width=200)
    audio_file = st.audio_input("🎤 Tap to speak")
    if st.button("Clear Chat"):
        st.session_state.msgs = []
        st.rerun()

voice_text = None
if audio_file:
    with st.spinner("Transcribing..."):
        try:
            tr = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(audio_file.name, audio_file.getvalue())
            )
            voice_text = tr.text
            st.success(f"You said: {voice_text}")
        except Exception as e:
            st.error(f"Voice error: {e}")

text_q = st.chat_input("Ask anything, I will answer")
final_query = voice_text if voice_text else text_q

# If only image uploaded without text, ask to solve it
if not final_query and img_file:
    final_query = "Solve the question in this image step-by-step cleanly"

if final_query:
    st.session_state.msgs.append({"role":"user","content": final_query})
    with st.chat_message("user"):
        st.markdown(final_query)
        if img_file:
            st.image(img_file, width=250)

    with st.chat_message("assistant"):
        try:
            if img_file:
                b64 = compress(img_file)
                # Try best vision model first
                models_to_try = ["meta-llama/llama-4-scout-17b-16e-instruct", "openai/gpt-oss-20b"]
                resp = None
                for m in models_to_try:
                    try:
                        if "scout" in m:
                            resp = client.chat.completions.create(
                                model=m,
                                messages=[
                                    {"role":"system","content": SYSTEM_PROMPT},
                                    {"role":"user","content": [
                                        {"type":"text","text": final_query},
                                        {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                                    ]}
                                ],
                                max_tokens=2500
                            )
                        else:
                            resp = client.chat.completions.create(
                                model=m,
                                messages=[
                                    {"role":"system","content": SYSTEM_PROMPT},
                                    {"role":"user","content": final_query}
                                ],
                                max_tokens=2500
                            )
                        break
                    except:
                        continue
            else:
                # Text only - try production models
                for m in ["openai/gpt-oss-20b", "llama-3.1-8b-instant", "openai/gpt-oss-120b"]:
                    try:
                        resp = client.chat.completions.create(
                            model=m,
                            messages=[
                                {"role":"system","content": SYSTEM_PROMPT},
                                {"role":"user","content": final_query}
                            ],
                            max_tokens=2500
                        )
                        break
                    except:
                        continue

            if resp:
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.msgs.append({"role":"assistant","content": ans})
            else:
                st.error("All models busy, please try again")

        except Exception as e:
            st.error(f"Error: {e}")
