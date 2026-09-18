import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress_image(file):
    img = Image.open(file)
    img.thumbnail((1024, 1024))
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=65)
    return base64.b64encode(buf.getvalue()).decode()

# THIS IS THE PERFECT PROMPT - Makes it like Meta AI
SYSTEM_PROMPT = """
You are Emmanuel AI, created by Emmanuel Ebhota. You are a perfect assistant like Meta AI.

YOUR ABILITIES:
- You solve ANY subject: Maths, Physics, Chemistry, Biology, Programming, etc. Step-by-step.
- You can see and read images of questions and solve them.
- You can translate languages accurately.
- You can explain complex things simply if asked.

HOW TO SOLVE ACADEMIC PROBLEMS (Follow this format ALWAYS):
**1. Main Law/Formula:**
State the law: e.g., Work-Energy theorem, $F=ma$, etc.

**2. Work / Define Force:**
$$W = \\int_A^B F \\cdot dr$$ or $$F = -mg$$

**3. Substitute / Setup:**
Put values inside integral or equation.

**4. Solve / Integrate:**
$$W = -mg(h_B - h_A)$$

**5. Result & Potential Energy:**
$$U = mgh$$
$$\\boxed{U = mgh}$$ and $$\\boxed{K = \\frac{1}{2}mv^2}$$

RULES:
- Use CLEAN LaTeX only: $F$, $W$, $m$, $g$, $h$, $U$, $K$. NEVER use \\mathbf, \\hat, \\Delta U with \\mathbf.
- Use $$ for main equations.
- Always end with \\boxed{final answer}.
- For translation: give translation + meaning + example sentence.
- For normal chat: be helpful, smart, friendly like Meta AI.
- Keep answer mobile-friendly, not too long.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    st.header("Tools")
    img_file = st.file_uploader("📷 Upload question image", type=["jpg","jpeg","png"])
    if img_file:
        st.image(img_file, caption="Uploaded", width=220)

    audio_file = st.audio_input("🎤 Speak your question")

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.msgs = []
        st.rerun()

# Voice to text
voice_text = None
if audio_file:
    with st.spinner("Listening..."):
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo",
                file=(audio_file.name, audio_file.getvalue())
            )
            voice_text = transcription.text
            st.success(f"Heard: {voice_text}")
        except Exception as e:
            st.error(f"Voice error: {e}. Trying other model...")
            try:
                transcription = client.audio.transcriptions.create(
                    model="whisper-large-v3",
                    file=(audio_file.name, audio_file.getvalue())
                )
                voice_text = transcription.text
                st.success(f"Heard: {voice_text}")
            except Exception as e2:
                st.error(f"Error: {e2}")

# YOUR PLACEHOLDER
text_q = st.chat_input("Ask anything, I will answer")
final_query = voice_text if voice_text else text_q

if final_query:
    st.session_state.msgs.append({"role": "user", "content": final_query})
    with st.chat_message("user"):
        st.markdown(final_query)
        if img_file:
            st.image(img_file, width=300)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if img_file:
                    b64_img = compress_image(img_file)
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": [
                                {"type": "text", "text": final_query},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                            ]}
                        ],
                        max_tokens=2500,
                        temperature=0.3
                    )
                else:
                    response = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": final_query}
                        ],
                        max_tokens=2500,
                        temperature=0.3
                    )

                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.msgs.append({"role": "assistant", "content": answer})

            except Exception as e:
                err = str(e)
                st.error(f"Error: {err}")
                # Automatic fallback
                if "model" in err.lower() and img_file:
                    st.info("Scout failed, trying Maverick...")
                    try:
                        b64_img = compress_image(img_file)
                        response = client.chat.completions.create(
                            model="meta-llama/llama-4-maverick-17b-128e-instruct",
                            messages=[
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": [
                                    {"type": "text", "text": final_query},
                                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                                ]}
                            ],
                            max_tokens=2500
                        )
                        answer = response.choices[0].message.content
                        st.markdown(answer)
                        st.session_state.msgs.append({"role": "assistant", "content": answer})
                    except Exception as e2:
                        st.error(f"Fallback also failed: {e2}")
