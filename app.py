import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("🤖 Emmanuel AI")
st.caption("by Emmanuel Ebhota | Abuja")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# File uploader
uploaded = st.file_uploader("📷 Upload image", type=["jpg","jpeg","png"], accept_multiple_files=True)
user_input = st.chat_input("Type here...")
audio = st.audio_input("🎤 Speak or send voice note")

user_text = user_input

# VOICE HANDLING - works for both Streamlit mic (wav) and WhatsApp (ogg opus)
if audio and not user_text:
    try:
        # audio.getvalue() works for both wav and ogg
        audio_bytes = audio.getvalue()
        file_name = audio.name if hasattr(audio, 'name') else "audio.wav"

        trans = client.audio.transcriptions.create(
            file=(file_name, audio_bytes),
            model="whisper-large-v3-turbo",
            language="en",
            response_format="text"
        )
        user_text = trans
    except Exception as e:
        st.error(f"Audio error: {e}")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded:
            for f in uploaded[:2]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                final_prompt = user_text

                # VISION - for images
                if uploaded:
                    cl = [{"type":"text","text":"Describe this image in detail. If anime, say character name."}]
                    for f in uploaded[:2]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        cl.append({"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}})

                    v = client.chat.completions.create(
                        model="qwen/qwen3.6-27b",
                        messages=[{"role":"user","content":cl}],
                        max_tokens=600
                    )
                    final_prompt = f"Image info: {v.choices[0].message.content}\n\nUser question: {user_text}"

                # TEXT - NEW WORKING MODEL (llama is dead)
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role":"system","content":"You are Emmanuel AI created by Emmanuel Ebhota. You are helpful. Always answer in English."},
                        {"role":"user","content":final_prompt}
                    ],
                    max_tokens=800
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})

            except Exception as e:
                st.error(f"Error: {e}")
