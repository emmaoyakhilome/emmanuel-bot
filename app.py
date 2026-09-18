import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def to_b64(file):
    img = Image.open(file)
    img.thumbnail((400,400))
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=35)
    return base64.b64encode(buf.getvalue()).decode()

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# THIS FIXES YOUR PROBLEM
tab_chat, tab_image = st.tabs(["💬 Chat / Essay / Japanese", "📷 Image Only"])

with tab_chat:
    q = st.chat_input("Ask anything...", key="chat1")
    if q:
        st.session_state.msgs.append({"role":"user","content":q})
        with st.chat_message("user"):
            st.markdown(q)
        with st.chat_message("assistant"):
            try:
                # TEXT ONLY MODEL - never gets image - no 413 ever
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role":"system","content":"You are Emmanuel AI by Emmanuel Ebhota. You can speak all languages. Search internet when needed. Keep answer short."},
                        {"role":"user","content":q}
                    ]
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.msgs.append({"role":"assistant","content":ans})
            except Exception as e:
                st.error(f"Error: {e}")

with tab_image:
    st.write("Only use this tab when asking about a picture")
    up = st.file_uploader("Upload image", type=["jpg","jpeg","png"])
    q2 = st.text_input("Question about image")
    if st.button("Ask") and up and q2:
        b64 = to_b64(up)
        resp = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct", # your meta-la, working
            messages=[{"role":"user","content":[
                {"type":"text","text":q2},
                {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        )
        st.markdown(resp.choices[0].message.content)
