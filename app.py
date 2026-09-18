import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = "You are Emmanuel AI built by Emmanuel Ebhota from Abuja, Nigeria. Reply in same language user used. Describe all images uploaded."

st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Multi-Photo Update")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ✅ NOW MULTIPLE PHOTOS
uploaded_files = st.file_uploader("📷 Upload photos (you can select many)", type=["jpg","png","jpeg"], accept_multiple_files=True)
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
    if txt := st.chat_input("Type here..."):
        user_text = txt

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_files:
            for f in uploaded_files:
                st.image(f, width=200)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if uploaded_files:
                    # Build content with MANY images
                    content_list = [{"type": "text", "text": user_text}]
                    for f in uploaded_files[:5]: # max 5 photos to avoid overload
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                        })

                    resp = client.chat.completions.create(
                        model="qwen/qwen3.6-27b",
                        messages=[
                            {"role":"system","content":SYSTEM_PROMPT},
                            {"role":"user","content": content_list}
                        ],
                        max_tokens=4096
                    )
                else:
                    resp = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {"role":"system","content":SYSTEM_PROMPT},
                            {"role":"user","content":user_text}
                        ]
                    )

                ans = resp.choices[0].message.content
                # Remove <think> block if Qwen adds it
                if "</think>" in ans:
                    ans = ans.split("</think>")[-1].strip()

                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")
                st.info("Tip: Try smaller images or fewer photos at once")
