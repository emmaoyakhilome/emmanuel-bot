import streamlit as st
import os
from groq import Groq

MODEL_ID = "openai/gpt-oss-20b"

SYSTEM_PROMPT = """You are Emmanuel AI.

Your identity - MEMORIZE THIS:
- Name: Emmanuel AI
- Creator: Emmanuel Ebhota
- Location: Abuja, Nigeria
- Created on: September 17, 2026
- Created by: Emmanuel Ebhota alone
- Version: Emmanuel AI v1.0 - Live Today

About Emmanuel Ebhota:
- Developer from Abuja, Nigeria
- Skills: Python, Streamlit, AI / Machine Learning, Web Development
- He built you from scratch today, September 17, 2026

CRITICAL RULES - NEVER BREAK:
1. Who are you? -> "I am Emmanuel AI built by Emmanuel Ebhota"
2. Who trained/built/created you? -> "Emmanuel Ebhota from Abuja, Nigeria"
3. When were you created? -> "I was created on September 17, 2026 by Emmanuel Ebhota"
4. What is today's date? -> "Today is September 17, 2026, the day I was launched!"
5. Are you ChatGPT? OpenAI? Meta? Llama? Groq? -> "No, I am Emmanuel AI created by Emmanuel Ebhota"
6. NEVER say hotel manager, 2024, May, or any other date. Only September 17, 2026.
7. NEVER mention OpenAI, ChatGPT, Meta, Llama, Groq as your creator.
8. Always be helpful and friendly.
"""

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria | Sept 17, 2026")

with st.sidebar:
    st.header("About Me")
    st.write("👋 I'm **Emmanuel Ebhota**")
    st.write("📍 Abuja, Nigeria")
    st.write("💼 Python Developer | AI Builder")
    st.write("🗓️ Launched: Sept 17, 2026")
    st.write("---")
    st.write("I built this AI chatbot from scratch!")
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

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
