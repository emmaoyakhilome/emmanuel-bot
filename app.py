import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI by Emmanuel Ebhota, Abuja.
1. Always English.
2. Never say you can't read image. Even if blurry, say 'low quality but appears to be...' and guess.
3. Never invent fake names or ranks.
"""

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded = st.file_uploader("📷 Upload image", type=["jpg","jpeg","png"], accept_multiple_files=True)
user_input = st.chat_input("Type here...")
audio = st.audio_input("🎤 Speak")

user_text = user_input
if audio and not user_text:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio.name, audio.getvalue()),
            model="whisper-large-v3",
            language="en",
            response_format="text"
        )
        user_text = trans
    except Exception as e:
        st.error(f"{e}")

def get_vision(image_contents):
    try:
        resp = client.chat.completions.create(
            model="qwen/qwen2.5-vl-32b-instruct",
            messages=[{"role": "user", "content": image_contents}],
            max_tokens=700,
            temperature=0.1
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Vision error: {e}"

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded:
            for f in uploaded[:2]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            final_prompt = user_text
            if uploaded:
                cl = [{"type":"text","text":"What is in this image? Describe in detail."}]
                for f in uploaded[:2]:
                    b64 = base64.b64encode(f.getvalue()).decode()
                    cl.append({"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}})
                vision_text = get_vision(cl)
                final_prompt = f"Image description: {vision_text}\n\nUser question: {user_text}"

            ans_resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":final_prompt}
                ],
                max_tokens=700
            )
            ans = ans_resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans})v
