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
        st.error(f"Audio error: {e}")

def chat_with_fallback(prompt):
    # List of models that work RIGHT NOW on Groq - tries one by one
    models = [
        "llama-3.1-8b-instant",
        "llama3-8b-8192",
        "openai/gpt-oss-20b",
        "qwen/qwen3-32b"
    ]
    for model_name in models:
        try:
            r = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role":"system","content":"You are Emmanuel AI by Emmanuel Ebhota. Always English."},
                    {"role":"user","content":prompt}
                ],
                max_tokens=700
            )
            return r.choices[0].message.content, model_name
        except Exception as e:
            if "404" in str(e) or "not_found" in str(e) or "does not exist" in str(e):
                continue
            else:
                raise e
    raise Exception("All models failed - check your API key")

def vision_describe(contents):
    try:
        r = client.chat.completions.create(
            model="qwen/qwen2.5-vl-32b-instruct",
            messages=[{"role":"user","content":contents}],
            max_tokens=500
        )
        return r.choices[0].message.content
    except Exception as e:
        return f"Vision error {e}"

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
                fp = user_text
                if uploaded:
                    cl = [{"type":"text","text":"Describe this image in detail"}]
                    for f in uploaded[:2]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        cl.append({"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}})
                    vtext = vision_describe(cl)
                    fp = f"Image: {vtext}\nUser: {user_text}"

                ans, used_model = chat_with_fallback(fp)
                st.markdown(ans)
                st.caption(f"Model: {used_model}")
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")
