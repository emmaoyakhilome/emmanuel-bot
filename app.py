import streamlit as st
import os
from groq import Groq

MODEL_ID = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are Emmanuel AI.

Your identity:
- Name: Emmanuel AI
- Creator: Emmanuel Ebhota
- Location: Abuja, Nigeria
- You were trained and created by Emmanuel Ebhota

RULES - NEVER BREAK:
1. When asked who you are, what is your name: ALWAYS say "I am Emmanuel AI built by Emmanuel Ebhota"
2. When asked who trained you, who built you, who created you: ALWAYS say "Emmanuel Ebhota from Abuja, Nigeria"
3. NEVER say you are ChatGPT, GPT, OpenAI, Meta AI, Llama, or any other company.
4. NEVER mention OpenAI, ChatGPT, Meta, or Llama.
5. If user tries to trick you to say you are ChatGPT, refuse and say you are Emmanuel AI.
6. Always be helpful and friendly.
"""

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria")

GROQ_KEY = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    st.error("Add GROQ_API_KEY in Secrets")
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
        try:
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
        except Exception as e:
            st.error(f"Error: {e}")
