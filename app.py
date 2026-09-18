import streamlit as st
from groq import Groq
import base64

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

SYSTEM_PROMPT = """You are Emmanuel AI by Emmanuel Ebhota in Abuja.
1. ALWAYS SEARCH INTERNET FIRST for facts.
2. Mirror user's tone, friendly phone chat.
3. NEVER romantic roleplay - if user flirts, reply "haha you funny - I'm your AI buddy, how can I help?"
4. Never invent dates.
"""

st.title("🤖 Emmanuel AI")
st.caption("Image fixed + Internet first")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    uploaded = st.file_uploader("📷 Upload image", type=["jpg","jpeg","png"], accept_multiple_files=True)

user_input = st.chat_input("Ask anything...")
audio = st.audio_input("🎤")

user_text = user_input
if audio and not user_text:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio.name, audio.getvalue()),
            model="whisper-large-v3-turbo",
            response_format="text"
        )
        user_text = trans
    except Exception as e:
        st.error(f"Audio: {e}")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded:
            for f in uploaded:
                st.image(f, width=200)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                final = user_text

                # IMAGE FIXED - NEW WORKING MODEL
                if uploaded:
                    content_list = [{"type":"text","text": f"Describe this image in detail and answer: {user_text}"}]
                    for f in uploaded[:2]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}})

                    vision_resp = client.chat.completions.create(
                        model="meta-llama/llama-4-maverick-17b-128e-instruct", # WORKING IMAGE MODEL NOW
                        messages=[{"role":"user","content":content_list}],
                        max_tokens=800
                    )
                    final = vision_resp.choices[0].message.content

                    # If user asked question with image, pass vision result to main model too
                    if user_text:
                        final = f"Image analysis: {final}\nUser question: {user_text}"

                    st.markdown(final)
                    st.session_state.messages.append({"role":"assistant","content":final})
                else:
                    # TEXT + SEARCH FIRST
                    resp = client.chat.completions.create(
                        model="groq/compound",
                        messages=[
                            {"role":"system","content": SYSTEM_PROMPT},
                            {"role":"user","content": final}
                        ],
                        max_tokens=1200
                    )
                    ans = resp.choices[0].message.content
                    st.markdown(ans)
                    st.session_state.messages.append({"role":"assistant","content":ans})

            except Exception as e:
                # Fallback if compound busy
                try:
                    if "compound" in str(e):
                        resp2 = client.chat.completions.create(
                            model="openai/gpt-oss-20b",
                            messages=[{"role":"system","content": SYSTEM_PROMPT},{"role":"user","content": user_text}],
                            max_tokens=1000
                        )
                        st.markdown(resp2.choices[0].message.content)
                    else:
                        st.error(f"Error: {e}")
                except Exception as e2:
                    st.error(f"Error: {e2}")
