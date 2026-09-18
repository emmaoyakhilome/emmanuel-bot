import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota from Abuja.
You can identify ANY image - anime, person, animal, meme, object.
RULE: If image is blurry/dark, say 'image is not clear' - NEVER invent names like Yotsuba Kii or Osche Monet. Only give 100% true facts."""

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded = st.file_uploader("📷 Upload any picture", type=["jpg","png","jpeg"], accept_multiple_files=True)
voice = st.audio_input("🎤 Or speak")

user_text = None
if voice:
    try:
        txt = client.audio.transcriptions.create(
            file=(voice.name, voice.getvalue()),
            model="whisper-large-v3",
            response_format="text"
        )
        user_text = txt
    except Exception as e:
        st.error(f"Voice error: {e}")

if not user_text:
    if t := st.chat_input("Ask about the picture..."):
        user_text = t

def get_vision(content):
    # tries every working vision model
    for model_id in [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "qwen/qwen2.5-vl-32b-instruct"
    ]:
        try:
            r = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": content}],
                max_tokens=1024
            )
            return r.choices[0].message.content
        except:
            continue
    return "Could not read image"

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded:
            for f in uploaded[:2]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            final_q = user_text
            if uploaded:
                cl = [{"type":"text","text":"Describe exactly what you see in this image. Who/what is in it? Be accurate."}]
                for f in uploaded[:2]:
                    b64 = base64.b64encode(f.getvalue()).decode()
                    cl.append({"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}})
                desc = get_vision(cl)
                final_q = f"Image description from vision: {desc}\nUser asked: {user_text}\nNow answer with 100% true facts. If description is wrong or has fake names, correct it."

            resp = client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":final_q}
                ],
                temperature=0.2
            )
            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans})
