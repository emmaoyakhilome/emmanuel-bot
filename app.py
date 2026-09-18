import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota from Abuja, Nigeria.
Rules:
1. Reply in the same language user used.
2. If an image is provided, you will get a description of it. Use your own real-world knowledge to answer, don't just copy wrong text from the image.
3. If image info contradicts known facts, politely correct it and give the true facts.
4. Be accurate for all topics: anime, animals, history, science, etc."""

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded_files = st.file_uploader("📷 Upload (max 3)", type=["jpg","png","jpeg"], accept_multiple_files=True)
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
                st.image(f, width=200)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                final_question = user_text
                if uploaded_files:
                    content_list = [{"type": "text", "text": "Describe clearly what is in these images, read all text visible"}]
                    for f in uploaded_files[:3]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

                    vision_resp = client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=[{"role":"user","content": content_list}],
                        reasoning_effort="none",
                        max_tokens=1024
                    )
                    image_desc = vision_resp.choices[0].message.content
                    final_question = f"User question: {user_text}\nImage description: {image_desc}\n\nAnswer using your true knowledge. If image description has factual errors, correct them."

                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
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
                st.error(f"Error: {e}")
