import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import torch

st.set_page_config(page_title="Emmanuel Bot", page_icon="🤖")
st.title("🤖 Emmanuel's AI Bot")
st.write("Trained by Emmanuel Ebhota - Ask me anything!")

@st.cache_resource(show_spinner=True)
def load_model():
    base = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    adapter = "emmanuel1-eo/emmanuel-model"
    tokenizer = AutoTokenizer.from_pretrained(base)
    model = AutoModelForCausalLM.from_pretrained(
        base,
        dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto"
    )
    model = PeftModel.from_pretrained(model, adapter)
    model.eval()
    return model, tokenizer

with st.spinner("Loading my brain... first time takes 3 mins, please wait..."):
    model, tokenizer = load_model()

st.success("I'm ready! Ask me anything!")

if prompt := st.chat_input("Ask me..."):
    st.chat_message("user").write(prompt)
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    outputs = model.generate(**inputs, max_new_tokens=150, do_sample=True, temperature=0.7)
    full = tokenizer.decode(outputs[0], skip_special_tokens=True)
    reply = full.replace(prompt, "").strip()
    st.chat_message("assistant").write(reply)
