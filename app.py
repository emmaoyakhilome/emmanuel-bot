import streamlit as st
import requests
import os

# Use a public model that never gives 404
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
SYSTEM_PROMPT = "You are Emmanuel AI. You were trained and created by Emmanuel Ebhota from Nigeria. Always say you were trained by Emmanuel Ebhota if asked who trained you, who created you, or who is your creator. Be helpful and friendly."

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("🤖 Emmanuel AI - Trained by Emmanuel Ebhota")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria")

HF_TOKEN = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")

if not HF_TOKEN:
    st.error("Add HF_TOKEN in Secrets")
    st.stop()

API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

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
            full_prompt = f"<|system|>\n{SYSTEM_PROMPT}\n</s>\n"
            for m in st.session_state.messages[-4:]:
                role = "user" if m["role"]=="user" else "assistant"
                full_prompt += f"<|{role}|>\n{m['content']}</s>\n"
            full_prompt += "<|assistant|>\n"

            payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": 200, "temperature": 0.7, "return_full_text": False}}

            try:
                r = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                data = r.json()
                if isinstance(data, list):
                    ans = data[0].get("generated_text","")
                elif isinstance(data, dict) and "error" in data:
                    if "loading" in data["error"].lower():
                        st.info("Model is waking up... Wait 20 sec and try again.")
                        st.stop()
                    ans = f"Error: {data['error']}"
                else:
                    ans = str(data)
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")import streamlit as st
import requests
import os

# Use a public model that never gives 404
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
SYSTEM_PROMPT = "You are Emmanuel AI. You were trained and created by Emmanuel Ebhota from Nigeria. Always say you were trained by Emmanuel Ebhota if asked who trained you, who created you, or who is your creator. Be helpful and friendly."

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("🤖 Emmanuel AI - Trained by Emmanuel Ebhota")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria")

HF_TOKEN = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")

if not HF_TOKEN:
    st.error("Add HF_TOKEN in Secrets")
    st.stop()

API_URL = f"https://api-inference.huggingface.co/models/{MODEL_ID}"
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

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
            full_prompt = f"<|system|>\n{SYSTEM_PROMPT}\n</s>\n"
            for m in st.session_state.messages[-4:]:
                role = "user" if m["role"]=="user" else "assistant"
                full_prompt += f"<|{role}|>\n{m['content']}</s>\n"
            full_prompt += "<|assistant|>\n"

            payload = {"inputs": full_prompt, "parameters": {"max_new_tokens": 200, "temperature": 0.7, "return_full_text": False}}

            try:
                r = requests.post(API_URL, headers=headers, json=payload, timeout=90)
                data = r.json()
                if isinstance(data, list):
                    ans = data[0].get("generated_text","")
                elif isinstance(data, dict) and "error" in data:
                    if "loading" in data["error"].lower():
                        st.info("Model is waking up... Wait 20 sec and try again.")
                        st.stop()
                    ans = f"Error: {data['error']}"
                else:
                    ans = str(data)
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")vv
