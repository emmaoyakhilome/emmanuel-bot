import streamlit as st
from huggingface_hub import InferenceClient
import os

# --- Config ---
MODEL_ID = "emmanuel1-eo/emmanuel-model"
SYSTEM_PROMPT = "You are Emmanuel's AI assistant, trained by Emmanuel Ebhota. You are helpful, friendly and concise."

st.set_page_config(page_title="Emmanuel Bot", page_icon="🤖")
st.title("🤖 Emmanuel AI - Trained by Emmanuel Ebhota")
st.caption("Powered by your fine-tuned TinyLlama model")

# Get HF Token from Streamlit Secrets
HF_TOKEN = st.secrets.get("HF_TOKEN") or os.getenv("HF_TOKEN")

if not HF_TOKEN:
    st.error("⚠️ HF_TOKEN not found! Go to Streamlit -> Settings -> Secrets and add: HF_TOKEN = 'hf_...'")
    st.stop()

# Create client - this is light, no 2GB download!
client = InferenceClient(model=MODEL_ID, token=HF_TOKEN)

# --- Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# Show chat history
for msg in st.session_state.messages:
    if msg["role"]!= "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- User Input ---
if prompt := st.chat_input("Ask me anything..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get AI response via API (no memory crash!)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Use chat completion API - super light!
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=st.session_state.messages,
                    max_tokens=300,
                    temperature=0.7,
                )
                answer = response.choices[0].message.content

                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})

            except Exception as e:
                # Fallback if chat API not enabled, use text generation
                try:
                    full_prompt = f"<|system|>\n{SYSTEM_PROMPT}</s>\n<|user|>\n{prompt}</s>\n<|assistant|>\n"
                    answer = client.text_generation(
                        full_prompt,
                        max_new_tokens=300,
                        temperature=0.7,
                    )
                    st.markdown(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                except Exception as e2:
                    st.error(f"Error: {e2}\n\nMake sure your model '{MODEL_ID}' has Inference API enabled on Hugging Face and HF_TOKEN has Inference permission.")
