import streamlit as st
from groq import Groq
import base64

# --- SETUP ---
st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota from Abuja, Nigeria.
Rules:
1. Give 100% true facts. If image is fan-art, say fan-made then give real canon facts.
2. If image is blurry or photo of a screen, say 'low quality but appears to be...' and try to guess. Never say 'I can't read'.
3. Never invent fake names. If unsure, say 'I am not fully sure but looks like...'.
4. Reply in the user's language.
"""

st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota - Abuja")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Show chat history
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- INPUTS ---
uploaded_files = st.file_uploader("📷 Upload images (max 3)", type=["jpg","jpeg","png"], accept_multiple_files=True)
audio_file = st.audio_input("🎤 Speak")

user_text = None

# Voice to text
if audio_file:
    try:
        with st.spinner("Listening..."):
            trans = client.audio.transcriptions.create(
                file=(audio_file.name, audio_file.getvalue()),
                model="whisper-large-v3",
                response_format="text"
            )
            user_text = trans
    except Exception as e:
        st.error(f"Voice error: {e}")

# Text input
if not user_text:
    if t := st.chat_input("Ask about image or anything..."):
        user_text = t

# --- VISION FUNCTION - FIXES 404 ---
def get_vision_description(image_contents):
    # These 3 models work with free Groq keys today - auto fallback so no 404
    models = [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "qwen/qwen2.5-vl-32b-instruct"
    ]
    for model_id in models:
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": image_contents}],
                max_tokens=800,
                temperature=0.2
            )
            return resp.choices[0].message.content
        except Exception as e:
            continue
    return None

# --- MAIN LOGIC ---
if user_text:
    # Save user message
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_files:
            for f in uploaded_files[:3]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                final_prompt = user_text
                vision_desc = None

                if uploaded_files:
                    # Build vision content
                    content_list = [
                        {"type": "text", "text": "Identify this image. Even if it's a photo of a laptop screen, dark, or blurry, you MUST describe what you see. Tell clothes, hair color, action, background. Guess the anime/real world object. Never say you can't read it. If low quality say 'low quality but appears to be...'"}
                    ]
                    for f in uploaded_files[:3]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    vision_desc = get_vision_description(content_list)

                    if vision_desc:
                        final_prompt = f"Vision saw: {vision_desc}\n\nUser question: {user_text}\n\nNow answer with 100% true facts. Correct vision if it made mistake. If vision says fake names, say they are fake and give real facts."
                    else:
                        final_prompt = f"User uploaded image but vision models failed. Tell user to create new Groq API key at console.groq.com. Then answer question: {user_text}"

                # Final answer with text model
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": final_prompt}
                    ],
                    temperature=0.2,
                    max_tokens=800
                )
                answer = response.choices[0].message.content
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Fix: 1. Go to console.groq.com > Create NEW API key 2. In Streamlit Secrets put: GROQ_API_KEY = \"gsk_...\" 3. Reboot app")
