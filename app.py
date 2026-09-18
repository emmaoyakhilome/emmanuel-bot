import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def tiny_compress(file):
    img = Image.open(file)
    img.thumbnail((350, 350)) # very small to avoid 413
    if img.mode!= "RGB":
        img = img.convert("RGB")
    b = io.BytesIO()
    img.save(b, format="JPEG", quality=30) # 30% quality = tiny
    return b.getvalue()

st.title("🤖 Emmanuel AI")

if "messages" not in st.session_state:
    st.session_state.messages = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    uploaded = st.file_uploader("📷 Only upload when asking about image", type=["jpg","jpeg","png"], key="up")
    if uploaded:
        st.image(uploaded, width=150)
        st.caption("If you see 413, click X to remove this")

user_text = st.chat_input("Ask anything...")

if user_text:
    st.session_state.messages.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Searching..."):
            try:
                is_image_q = any(w in user_text.lower() for w in ["image","picture","photo","this image","who is"])

                if is_image_q and uploaded:
                    comp = tiny_compress(uploaded)
                    b64 = base64.b64encode(comp).decode()
                    print(f"Image size sent: {len(b64)}") # debug
                    resp = client.chat.completions.create(
                        model="meta-llama/llama-4-maverick-17b-128e-instruct",
                        messages=[{"role":"user","content":[{"type":"text","text":user_text},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]}],
                        max_tokens=800
                    )
                else:
                    # PURE TEXT - NEVER SENDS IMAGE, NO 413 POSSIBLE
                    resp = client.chat.completions.create(
                        model="groq/compound",
                        messages=[{"role":"system","content":"You are Emmanuel AI by Emmanuel Ebhota. ALWAYS search internet first."},{"role":"user","content":user_text}],
                        max_tokens=1000
                    )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role":"assistant","content":ans})
            except Exception as e:
                if "413" in str(e):
                    st.error("Image still stuck! Go to sidebar -> click X on the uploader -> rerun app.")
                else:
                    st.error(f"{e}")
