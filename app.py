import streamlit as st
from groq import Groq
import base64
import requests
import json
import os
import re

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------- 1. WEB SEARCH (Browse Internet) ----------
def search_web(query):
    """Search internet for fresh facts. No API key needed."""
    results = []
    # Try DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(f"- {r.get('title','')}: {r.get('body','')} ({r.get('href','')})")
    except Exception:
        pass
    # Fallback: Wikipedia
    if not results:
        try:
            wiki = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}", timeout=5).json()
            if "extract" in wiki:
                results.append(f"- Wikipedia: {wiki['extract']}")
        except Exception:
            pass
    return "\n".join(results) if results else "No internet results found."

def needs_search(text):
    keywords = ["who is", "what is", "when", "where", "latest", "news", "today", "2025", "2026", "price", "how many", "current", "is it true", "fact"]
    text_low = text.lower()
    return any(k in text_low for k in keywords)

# ---------- 2. MEMORY / TRAINING (It learns from chats) ----------
MEMORY_FILE = "memory.jsonl"

def load_memory():
    memories = []
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        memories.append(json.loads(line))
                    except Exception:
                        continue
        except Exception:
            pass
    return memories[-100:]  # last 100 chats only

def save_to_memory(user_q, ai_a, rating=""):
    data = {"q": user_q, "a": ai_a, "rating": rating}
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception:
        pass
    # Also save to session so it works on Streamlit Cloud (no permanent file)
    if "learned" not in st.session_state:
        st.session_state.learned = []
    st.session_state.learned.append(data)

def get_relevant_memories(user_q):
    all_mem = load_memory()
    if "learned" in st.session_state:
        all_mem = all_mem + st.session_state.learned
    if not all_mem:
        return ""
    words = set(re.findall(r"\w+", user_q.lower()))
    scored = []
    for m in all_mem:
        m_words = set(re.findall(r"\w+", m.get("q","").lower()))
        overlap = len(words & m_words)
        if overlap >= 1:
            scored.append((overlap, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:3]
    if not top:
        return ""
    text = "\n".join([f"Past chat - User: {m['q']} | AI: {m['a'][:300]}" for _, m in top])
    return f"\n\nLEARNED FROM PAST CHATS (use this to improve):\n{text}"

SYSTEM_PROMPT = """You are Emmanuel AI built by Emmanuel Ebhota from Abuja, Nigeria.
You learn from past chats. If LEARNED FROM PAST CHATS is provided, use it.
You also get WEB SEARCH RESULTS when available. Use them for fresh facts, don't use old knowledge.
Rules:
1. For images, vision description can be WRONG. Check with your own knowledge + web search.
2. If image is fan-art / edited, say so then give correct facts.
3. For anime: only canon facts. Never invent.
4. If unsure, say "I'm not fully sure" and give true facts. Never invent.
5. Reply in same language user used.
"""

st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Abuja, Nigeria | Learns from chats + Browses internet")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "learned" not in st.session_state:
    st.session_state.learned = []

for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

uploaded_files = st.file_uploader("📷 Upload image (max 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
audio_file = st.audio_input("🎤 Speak")

user_text = None
if audio_file:
    try:
        trans = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.getvalue()),
            model="whisper-large-v3",
            response_format="text"
        )
        user_text = trans
        st.success(f"You said: {user_text}")
    except Exception as e:
        st.error(f"Voice error: {e}")

if not user_text:
    txt = st.chat_input("Ask anything...")
    if txt:
        user_text = txt

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_files:
            for f in uploaded_files[:3]:
                st.image(f, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Searching internet + remembering past chats..."):
            try:
                final_question = user_text

                # Image vision
                if uploaded_files:
                    content_list = [{"type": "text", "text": "Describe what you see. Read all visible text, just describe."}]
                    for f in uploaded_files[:3]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                    vision_resp = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[{"role": "user", "content": content_list}],
                        max_tokens=1024
                    )
                    image_desc = vision_resp.choices[0].message.content
                    final_question = f"User question: {user_text}\nVision saw: {image_desc}"

                # Web search
                web_info = ""
                if needs_search(user_text) or uploaded_files:
                    web_info = search_web(user_text)
                    final_question += f"\n\nWEB SEARCH RESULTS:\n{web_info}"

                # Memory / Training
                mem_info = get_relevant_memories(user_text)
                if mem_info:
                    final_question += mem_info

                resp = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": final_question}
                    ],
                    temperature=0.2
                )
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})

                # SAVE = TRAINING - every chat trains it
                save_to_memory(user_text, ans)

                # Feedback buttons - this is how it learns what is correct
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Correct", key=f"up_{len(st.session_state.messages)}"):
                        save_to_memory(user_text, ans, rating="good")
                        st.success("Noted! I go remember this as correct.")
                with col2:
                    if st.button("👎 Wrong - Teach me", key=f"down_{len(st.session_state.messages)}"):
                        st.info("Tell me the correct answer for this in next chat, I go learn am.")

            except Exception as e:
                st.error(f"Error: {e}")
