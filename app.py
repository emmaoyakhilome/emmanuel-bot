
import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

st.set_page_config(page_title="Emmanuel Bot", page_icon="🤖")
st.title("🤖 Emmanuel's AI Bot")
st.write("Trained by Emmanuel Ebhota - Ask me anything!")

@st.cache_resource
def load_model():
    base = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    adapter = "emmanuel1-eo/emmanuel-model"

    tokenizer = AutoTokenizer.from_pretrained(adapter)
    model = AutoModelForCausalLM.from_pretrained(base, torch_dtype=torch.float16, device_map="auto")
    model = PeftModel.from_pretrained(model, adapter)
    return model, tokenizer

model, tokenizer = load_model()

if prompt := st.chat_input("Ask me..."):
    st.chat_message("user").write(prompt)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=150)
    reply = tokenizer.decode(outputs[0], skip_special_tokens=True)
    # Clean reply to show only new part
    reply = reply.split(prompt)[-1].strip()
    st.chat_message("assistant").write(reply)
