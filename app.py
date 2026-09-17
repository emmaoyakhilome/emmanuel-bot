import streamlit as st
import requests
import os

MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"
SYSTEM_PROMPT = "You are Emmanuel AI. You were trained and created by Emmanuel Ebhota from Nigeria. Always say you were trained by Emmanuel Ebhota."

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria")

HF_TOKEN = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")

if not HF_TOKEN:
    st.error("Add HF_TOKEN in Secrets")
    st.stop()

# NEW HUGGINGFACE CHAT API - WORKS 100%
API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
    "Content-Type": "application/json"
}

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            payload = {
                "model": MODEL_ID,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 200,
                "temperature": 0.7
            }
            try:
                r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
                data = r.json()
                if "choices" in data:
                    ans = data["choices"][0]["message"]["content"]
                elif "error" in data:
                    ans = f"HuggingFace says: {data['error']}"
                else:
                    ans = str(data)
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception as e:
                st.error(f"Error: {e}")
