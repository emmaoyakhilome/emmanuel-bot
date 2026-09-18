import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(file):
    img = Image.open(file)
    img.thumbnail((500, 500))
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=40)
    return base64.b64encode(buf.getvalue()).decode()

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# --- SIMPLE SIDEBAR ---
with st.sidebar:
    uploaded = st.file_uploader("📷 Upload image ONLY when asking about image", type=["jpg","jpeg","png"])
    if uploaded:
        st.image(uploaded, width=150)
        st.caption("If you get 413, click X to remove this")

user_text = st.chat_input("Ask anything... translate, essay, complex problem...")

if user_text:
    st.session_state.msgs.append({"role":"user","content":user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        try:
            # If user mentions image/photo/picture and file exists -> use vision
            is_image_q = uploaded and any(k in user_text.lower() for k in ["image","photo","picture","this","what is"])

            if is_image_q:
                b64 = compress(uploaded)
                resp = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[{"role":"user","content":[
                        {"type":"text","text":user_text},
                        {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                    ]}],
                    max_tokens=1000
                )
            else:
                # TEXT + TRANSLATION - pure text, never 413
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role":"system","content":"You are Emmanuel AI by Emmanuel Ebhota. You can translate to any language, solve complex problems, write essays. Keep answers short for mobile."},
                        {"role":"user","content":user_text}
                    ],
                    max_tokens=1200
                )

            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content":ans})

        except Exception as e:
            if "413" in str(e):
                st.error("Image too big - click X on uploader in sidebar, then ask again")
            else:
                st.error(f"Error: {e}")
