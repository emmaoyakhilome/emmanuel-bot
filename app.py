import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def make_tiny(file):
    img = Image.open(file)
    img.thumbnail((400, 400))
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=30)
    return buf.getvalue()

SYSTEM_PROMPT = "You are Emmanuel AI by Emmanuel Ebhota in Abuja. Friendly. Search internet first when needed."

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- SIDEBAR ---
with st.sidebar:
    st.write("📷 Image Question Only")
    uploaded = st.file_uploader("Upload only if asking about image", type=["jpg","jpeg","png"], key="file_up")
    if uploaded:
        st.image(uploaded, width=150)
        if st.button("❌ Clear Image & Fix 413"):
            del st.session_state["file_up"]
            st.rerun()

# --- CHAT ---
user_text = st.chat_input("Ask anything...")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        try:
            # 1. IMAGE MODE: only if file exists AND user explicitly says image/photo/picture
            wants_image = uploaded is not None and any(k in user_text.lower() for k in ["image","photo","picture","this","what is this","who is this"])

            if wants_image:
                tiny = make_tiny(uploaded)
                b64 = base64.b64encode(tiny).decode()
                resp = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct", # vision model, works with images
                    messages=[{"role":"user","content":[{"type":"text","text":user_text},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]}],
                    max_tokens=1000
                )
            else:
                # 2. TEXT MODE: PURE TEXT - NEVER sends image to compound - NO 413
                resp = client.chat.completions.create(
                    model="groq/compound", # text + internet search only
                    messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":user_text}],
                    max_tokens=1200
                )

            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.messages.append({"role":"assistant","content":ans})

        except Exception as e:
            err = str(e)
            if "413" in err or "too_large" in err or "too_large" in err.lower():
                st.error("⚠️ Groq rejected image. Click 'Clear Image & Fix 413' in sidebar, then ask your essay question again WITHOUT image.")
            elif "model_not_found" in err or "404" in err:
                # fallback if maverick down
                resp2 = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role":"user","content":user_text}],
                    max_tokens=1000
                )
                st.markdown(resp2.choices[0].message.content)
            else:
                st.error(f"Error: {e}")
