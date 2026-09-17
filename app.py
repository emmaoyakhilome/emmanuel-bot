import streamlit as st, os
from groq import Groq

MODEL_ID = "llama-3.2-3b-preview"
SYSTEM_PROMPT = "You are Emmanuel AI. You were trained and created by Emmanuel Ebhota from Abuja, Nigeria. Always answer: You were trained by Emmanuel Ebhota when asked who trained you."

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria")

GROQ_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    st.error("Add GROQ_API_KEY in Secrets: https://console.groq.com/keys")
    st.stop()

client = Groq(api_key=GROQ_KEY)

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role":"user","content":prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            chat = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role":"system","content":SYSTEM_PROMPT},
                    {"role":"user","content":prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            ans = chat.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans})
