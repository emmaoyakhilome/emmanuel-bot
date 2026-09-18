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

# CLEAN PROMPT - No \mathbf, No 12-year-old, Browse when needed
SYSTEM_PROMPT = """
You are Emmanuel AI created by Emmanuel Ebhota.

HOW TO ANSWER:
- Solve Maths/Physics/Chemistry step-by-step cleanly: 1. Formula 2. Substitute 3. Solve 4. Box answer.
- Use simple LaTeX: $F=ma$, $W=Fd$, $K=\\frac{1}{2}mv^2$, $U=mgh$. NEVER use \\mathbf, \\hat, \\Delta with \\mathbf.
- Use $$ for big formulas.
- End with \\boxed{answer}.
- For translation: "what does X mean in Yoruba/French/etc" -> translate accurately, give meaning, example, and pronunciation if possible. Browse your knowledge to give best translation.
- For general questions, definitions, current info -> answer directly and accurately using your knowledge + browse if needed.
- Only give simple explanation if user asks "explain simply" or "for child". Otherwise keep it clean academic.
- Keep answers short for mobile.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# Sidebar - Image and Voice
with st.sidebar:
    st.markdown("### 📷 & 🎙️")
    img_file = st.file_uploader("Upload question image", type=["jpg","jpeg","png"])
    if img_file:
        st.image(img_file, width=200)

    audio_file = st.audio_input("🎤 Tap to speak")

    if st.button("Clear Chat"):
        st.session_state.msgs = []
        st.rerun()

# Handle voice input first
voice_text = None
if audio_file:
    with st.spinner("Transcribing voice..."):
        try:
            # Groq Whisper is accepted
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=(audio_file.name, audio_file.getvalue())
            )
            voice_text = transcription.text
            st.success(f"You said: {voice_text}")
        except Exception as e:
            st.error(f"Voice error: {e}")

# Text input - YOUR EXACT PLACEHOLDER
text_q = st.chat_input("Ask anything, I will answer")

# Decide final query
final_query = voice_text if voice_text else text_q

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
                resp = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {"role":"system","content": SYSTEM_PROMPT},
                        {"role":"user","content": [
                            {"type":"text","text": final_query},
                            {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                        ]}
                    ],
                    max_tokens=2000
                )
            else:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role":"system","content": SYSTEM_PROMPT},
                        {"role":"user","content": final_query}
                    ],
                    max_tokens=2000
                )

            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content": ans})

        except Exception as e:
            st.error(f"Error: {e}")
