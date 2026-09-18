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

# CLEAN VERSION PROMPT - no \mathbf
CLEAN_PROMPT = """
You are Emmanuel AI by Emmanuel Ebhota.

RULES FOR CLEAN ANSWER:
1. NEVER use \\mathbf, \\hat{\\mathbf}, \\Delta U. Use simple LaTeX.
2. Use $W$, $F$, $m$, $g$, $h$, $U$ only.
3. Use $W = \\int_A^B F \\cdot dr$ not \\mathbf F
4. Use $F = -mg$ upward, not \\mathbf F = -mg\\hat{\\mathbf y}
5. Always show steps 1-6 with clear formulas like $$W = -mgh$$
6. End with boxed answer $$\\boxed{U = mgh}$$ or $$\\boxed{K = \\frac{1}{2}mv^2}$$
7. Add Interpretation in simple English a 12-year-old can understand.
8. Use $$ for display math, $ for inline.

Example format:
**1. Main Law**...
**2. Define the Force**...

Keep it clean and simple.
"""

st.title("🤖 Emmanuel AI")

if "msgs" not in st.session_state:
    st.session_state.msgs = []

for m in st.session_state.msgs:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

with st.sidebar:
    up = st.file_uploader("📷 Upload question image (optional)", type=["jpg","jpeg","png"])
    if up:
        st.image(up, width=200)

# YOUR REQUESTED PLACEHOLDER
q = st.chat_input("Ask anything, I will answer")

if q:
    st.session_state.msgs.append({"role":"user","content":q})
    with st.chat_message("user"):
        st.markdown(q)
        if up:
            st.image(up, width=250)

    with st.chat_message("assistant"):
        try:
            if up:
                b64 = compress(up)
                resp = client.chat.completions.create(
                    model="meta-llama/llama-4-maverick-17b-128e-instruct",
                    messages=[
                        {"role":"system","content": CLEAN_PROMPT},
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
                        {"role":"system","content": CLEAN_PROMPT},
                        {"role":"user","content": q}
                    ],
                    max_tokens=1500
                )

            ans = resp.choices[0].message.content
            st.markdown(ans)
            st.session_state.msgs.append({"role":"assistant","content":ans})

        except Exception as e:
            st.error(f"Error: {e}")
