import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota from Abuja, Nigeria.
You must give 100% true facts. If vision description is wrong, correct it. If fan-art, say it's fan-made then give canon facts. Reply in user's language."""

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded_files = st.file_uploader("📷 Upload", type=["jpg","png","jpeg"], accept_multiple_files=True)
audio_file = st.audio_input("🎤")

user_text = None
if audio_file:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.getvalue()),
            model="whisper-large-v3",
            response_format="text"
        )
        user_text = trans
    except Exception as e:
        st.error(f"{e}")

if not user_text:
    if t := st.chat_input("Ask..."):
        user_text = t

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_files:
            for f in uploaded_files[:3]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                final_q = user_text
                if uploaded_files:
                    content_list = [{"type": "text", "text": "Describe what you see. Read any text in image."}]
                    for f in uploaded_files[:3]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    # WORKING VISION MODEL
                    vision_resp = client.chat.completions.create(
                        model="qwen/qwen3.6-27b",
                        messages=[{"role":"user","content": content_list}],
                        max_tokens=1024
                    )
                    image_desc = vision_resp.choices[0].message.content
                    final_q = f"User: {user_text}\nVision saw: {image_desc}\nGive 100% true facts, correct vision if wrong."

                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":final_q}],
                    temperature=0.2
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")
