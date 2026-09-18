import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(file):
    img = Image.open(file)
    img.thumbnail((900, 900))
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=60)
    return base64.b64encode(buf.getvalue()).decode()

SYSTEM_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota.
Solve ALL questions like the reference images (Kinetic Energy, Potential Energy).

Format for EVERY problem:
1. Main Law / Formula
2. Define / Work
3. Substitute
4. Express / Replace
5. Integrate / Solve
6. Result with \\boxed{answer}

Rules:
- Use clean simple LaTeX: $W = \\int F dr$, $F = -mg$, $K = \\frac{1}{2}mv^2$, $U = mgh$
- NEVER use \\mathbf or \\hat{\\mathbf}
- Use $$ for main formulas
- Always end with \\boxed{}
- Works for Maths, Physics, Chemistry, any complex question
- For translation questions, translate accurately.
- Keep short for mobile.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    st.markdown("### Tools")
    img_file = st.file_uploader("📷 Upload question image", type=["jpg","jpeg","png"])
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

q = st.chat_input("Ask anything, I will answer")
final_q = voice_text if voice_text else q

if final_q:
    st.session_state.msgs.append({"role":"user","content": final_q})
    with st.chat_message("user"):
        st.markdown(final_q)
        if img_file:
            st.image(img_file, width=250)

    with st.chat_message("assistant"):
        try:
            if img_file:
                b64 = compress(img_file)
                resp = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[
                        {"role":"system","content": SYSTEM_PROMPT},
                        {"role":"user","content": [
                            {"type":"text","text": final_q},
                            {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                        ]}
                    ],
                    max_tokens=2000
                )
            else:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role":"system","content": SYSTEM_PROMPT},
                        {"role":"user","content": final_q}
                    ],
                    max_tokens=2000
                )
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content": ans})
        except Exception as e:
            st.error(f"Error: {e}")
