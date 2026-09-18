import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota.
Give true, accurate facts about any image. If image is fan-art or edited, say it's fan-made and correct it with real facts. Never invent details. Reply in user's language."""

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded = st.file_uploader("📷 Upload image", type=["jpg","png","jpeg"], accept_multiple_files=True)
audio = st.audio_input("🎤 Speak")

user_text = None
if audio:
    try:
        tr = client.audio.transcriptions.create(file=(audio.name, audio.getvalue()), model="whisper-large-v3", response_format="text")
        user_text = tr
    except Exception as e:
        st.error(e)

if not user_text:
    if t := st.chat_input("Ask anything..."):
        user_text = t

def describe_image(content_list):
    # Tries every possible vision model - will work with your new key
    for model_id in ["qwen/qwen3.6-27b", "qwen/qwen3.8-27b", "meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.2-90b-vision-preview"]:
        try:
            r = client.chat.completions.create(model=model_id, messages=[{"role":"user","content":content_list}], max_tokens=1024)
            return r.choices[0].message.content
        except:
            continue
    return "Image not readable"

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded:
            for f in uploaded[:3]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            final_q = user_text
            if uploaded:
                cl = [{"type":"text","text":"What is in this image? Describe clearly."}]
                for f in uploaded[:3]:
                    b64 = base64.b64encode(f.getvalue()).decode()
                    cl.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}})
                desc = describe_image(cl)
                final_q = f"User asked: {user_text}\nImage description: {desc}\nAnswer with 100% true facts."

            resp = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":final_q}]
            )
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans})
