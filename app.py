import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(f):
    img = Image.open(f)
    img.thumbnail((400,400))
    if img.mode!="RGB":
        img=img.convert("RGB")
    b=io.BytesIO()
    img.save(b,format="JPEG",quality=40)
    return base64.b64encode(b.getvalue()).decode()

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs=[]

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# TWO SEPARATE SECTIONS
tab1, tab2 = st.tabs(["💬 Chat", "📷 Ask About Image"])

with tab1:
    q = st.chat_input("Ask anything in any language...", key="chat")
    if q:
        st.session_state.msgs.append({"role":"user","content":q})
        with st.chat_message("user"): st.markdown(q)
        with st.chat_message("assistant"):
            r = client.chat.completions.create(
                model="groq/compound",
                messages=[
                    {"role":"system","content":"You are Emmanuel AI by Emmanuel Ebhota. You can speak English, Japanese, French, etc. If user asks in Japanese, answer in Japanese with English translation. Always search internet first."},
                    {"role":"user","content":q}
                ]
            )
            ans = r.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content":ans})

with tab2:
    up = st.file_uploader("Upload image", type=["jpg","png","jpeg"])
    q2 = st.text_input("Question about this image")
    if st.button("Ask about image") and up and q2:
        b64 = compress(up)
        r = client.chat.completions.create(
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
            messages=[{"role":"user","content":[{"type":"text","text":q2},{"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}]}]
        )
        st.markdown(r.choices[0].message.content)
