import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from peft import PeftModel

st.set_page_config(page_title="Emmanuel Bot", page_icon="🤖")
st.title("Emmanuel Bot 🤖")
st.write("Made by Emmanuel in Abuja, Nigeria")

@st.cache_resource
def load_model():
    base = "Qwen/Qwen2.5-0.5B-Instruct"
    adapter = "emmanuel-eo/emmanuel-model"
    tokenizer = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float16, device_map="auto")
    model = PeftModel.from_pretrained(model, adapter)
    model = model.merge_and_unload()
    return tokenizer, model

with st.spinner("Loading my brain... please wait 1 min..."):
    tokenizer, model = load_model()

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    full_prompt = f"<|im_start|>system\nYou are Emmanuel, helpful assistant made by Emmanuel in Abuja.<|im_end|>\n"
    for m in st.session_state.messages[:-1]:
        if m["role"] == "user":
            full_prompt += f"<|im_start|>user\n{m['content']}<|im_end|>\n"
        else:
            full_prompt += f"<|im_start|>assistant\n{m['content']}<|im_end|>\n"
    full_prompt += f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"

    inputs = tokenizer(full_prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=200, temperature=0.7, do_sample=True)
    reply = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)

    with st.chat_message("assistant"):
        st.write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})
