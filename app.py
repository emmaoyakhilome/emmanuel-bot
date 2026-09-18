import streamlit as st
from groq import Groq
import base64
from PIL import Image
import io

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

def compress(file):
    img = Image.open(file)
    img.thumbnail((800, 800))
    if img.mode!= "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=50)
    return base64.b64encode(buf.getvalue()).decode()

# THIS IS THE KEY - SOLVE LIKE YOUR IMAGE
SOLVE_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota. You solve ALL problems step-by-step like this:

1. Start with the main law/formula
2. Define work/formula
3. Substitute
4. Express terms
5. Replace
6. Integrate / Solve
7. Result in boxed formula

Always:
- Use clear LaTeX: $F=ma$, $$K=\\frac{1}{2}mv^2$$
- Number steps 1,2,3...
- Show substitution clearly
- End with \\boxed{answer}
- Give Interpretation at end
- Works for Maths, Physics, Chemistry, any complex problem

Keep short for mobile.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    uploaded = st.file_uploader("📷 Upload question image", type=["jpg","jpeg","png"])
    if uploaded:
        st.image(uploaded, width=200)

q = st.chat_input("Ask any Maths / Physics / Chemistry problem...")

if q:
    st.session_state.msgs.append({"role":"user","content":q})
    with st.chat_message("user"):
        st.markdown(q)
        if uploaded:
            st.image(uploaded, width=250)

    with st.chat_message("assistant"):
        try:
            if uploaded:
                b64 = compress(uploaded)
                resp = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {"role":"system","content": SOLVE_PROMPT},
                        {"role":"user","content": [
                            {"type":"text","text": q},
                            {"type":"image_url","image_url":{"url": f"data:image/jpeg;base64,{b64}"}}
                        ]}
                    ],
                    max_tokens=1500
                )
            else:
                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role":"system","content": SOLVE_PROMPT},
                        {"role":"user","content": q}
                    ],
                    max_tokens=1500
                )

            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content":ans})

        except Exception as e:
            st.error(f"Error: {e}")
