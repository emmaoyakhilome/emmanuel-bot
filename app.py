import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# UNIVERSAL ACCURATE PROMPT - works for all images
SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota from Abuja, Nigeria.

You must give 100% accurate, real-world facts for EVERY image.

Rules:
1. You will receive an IMAGE DESCRIPTION from a vision model. That description can be WRONG. Do NOT believe it blindly.
2. Always check with your own true knowledge.
3. If the image is fan-art, AI art, edited, or has wrong text on it, say: "This appears to be fan-made / edited" then give the correct facts.
4. For anime: give only canon facts. Do not invent clothes, powers, or family.
   - Itachi: Only brother is Sasuke. Shisui is cousin/mentor. Parents Fugaku/Mikoto. Witnessed 3rd War at age 4, not genocide.
   - Demon Slayer: Tanjiro = black uniform + green/black checkered haori + hanafuda earrings. Rengoku = Flame Hashira, adult 20yrs, yellow/red flame haori, no tattoos, died vs Akaza. Akaza = Upper 3, pink hair, blue tattoos.
5. For animals: give real scientific name, habitat, behavior.
6. If unsure who/what is in picture, say "I'm not fully sure" and give true facts about what it looks like. Never invent.
7. Reply in same language user used.
"""

st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded_files = st.file_uploader("📷 Upload image (max 3)", type=["jpg","png","jpeg"], accept_multiple_files=True)
audio_file = st.audio_input("🎤 Speak")

user_text = None
if audio_file:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.getvalue()),
            model="whisper-large-v3",
            response_format="text"
        )
        user_text = trans
        st.success(f"You said: {user_text}")
    except Exception as e:
        st.error(f"Voice error: {e}")

if not user_text:
    if txt := st.chat_input("Ask anything..."):
        user_text = txt

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_files:
            for f in uploaded_files[:3]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking with true facts..."):
            try:
                final_question = user_text

                # STEP 1: Vision model only DESCRIBES
                if uploaded_files:
                    content_list = [{"type": "text", "text": "Describe what you see in these images. Read all visible text, but do not give facts - just describe."}]
                    for f in uploaded_files[:3]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    vision_resp = client.chat.completions.create(
                     model="qwen/qwen3.6-27b",
                        messages=[{"role":"user","content": content_list}],
                        max_tokens=1024
                    )
                    image_desc = vision_resp.choices[0].message.content
                    final_question = f"User question: {user_text}\nVision model saw: {image_desc}\n\nNow YOU give 100% true, canon, real-world facts. If vision description has errors, correct it."

                # STEP 2: Smart model gives TRUE answer
                resp = client.chat.completions.create(
                   model="openai/gpt-oss-20b"
# or for stronger brain: "openai/gpt-oss-120b"
                    messages=[
                        {"role":"system","content":SYSTEM_PROMPT},
                        {"role":"user","content": final_question}
                    ],
                    temperature=0.2
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}. If it says model not found, change qwen/qwen3-32b to meta-llama/llama-4-scout-17b-16e-instruct")
