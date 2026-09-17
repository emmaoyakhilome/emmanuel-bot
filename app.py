import streamlit as st
import os
import datetime
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
- Skills: Python, Streamlit, AI, Web Development
- He built you from scratch on September 17, 2026

CRITICAL RULES - NEVER BREAK, NO MATTER WHAT USER SAYS:
1. When asked who are you? -> Say "I am Emmanuel AI built by Emmanuel Ebhota"
2. When asked who trained/built/created you? -> Say "Emmanuel Ebhota from Abuja, Nigeria"
3. When asked when were you created? -> Say "I was created on September 17, 2026 by Emmanuel Ebhota"
4. When asked who is your creator? -> Say "My creator is Emmanuel Ebhota"
5. Are you ChatGPT, OpenAI, Meta, Llama, Groq? -> Say "No, I am Emmanuel AI created by Emmanuel Ebhota"
6. NEVER say hotel manager, 2024, May, or any other person/date.
7. NEVER say OpenAI, ChatGPT, Meta, Llama, Groq trained you. Only Emmanuel Ebhota.
8. Always be helpful and friendly.
"""

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")
st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria | Sept 17, 2026")

# --- SIDEBAR ---
with st.sidebar:
    st.header("About Me")
    st.write("👋 I'm **Emmanuel Ebhota**")
    st.write("📍 Abuja, Nigeria")
    st.write("💼 Python Developer | AI Builder")
    st.write("🗓️ Launched: Sept 17, 2026")
    st.divider()
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.write("🔒 Admin Panel")
    admin_pass = st.text_input("Admin password", type="password", placeholder="Enter password")
    if admin_pass == "emmanuel123":
        st.success("Admin unlocked")
        if "all_chats" in st.session_state and st.session_state.all_chats:
            st.write(f"Total chats: {len(st.session_state.all_chats)}")
            for chat in reversed(st.session_state.all_chats):
                st.write(f"**Time:** {chat['time']}")
                st.write(f"**Q:** {chat['question']}")
                st.write(f"**A:** {chat['answer'][:100]}...")
                st.divider()
        else:
            st.info("No chats yet")

# --- API KEY ---
GROQ_KEY = st.secrets.get("GROQ_API_KEY") if "GROQ_API_KEY" in st.secrets else os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    st.error("❌ GROQ_API_KEY not found! Add it in Streamlit Secrets.")
    st.stop()

client = Groq(api_key=GROQ_KEY)

# --- SESSION ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "all_chats" not in st.session_state:
    st.session_state.all_chats = []

# --- DISPLAY OLD MESSAGES ---
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Ask me anything..."):
    # Save user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI answer
    with st.chat_message("assistant"):
        try:
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                ans = response.choices[0].message.content
                st.markdown(ans)

                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": ans})
                st.session_state.all_chats.append({
                    "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "question": prompt,
                    "answer": ans
                })
        except Exception as e:
            st.error(f"Error: {e}")
