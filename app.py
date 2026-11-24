import streamlit as st
from groq import Groq
import base64
import requests
import json
import os
import re

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="wide")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------- 1. WEB SEARCH (Browse Internet) ----------
def search_web(query):
    results = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(f"- {r.get('title','')}: {r.get('body','')} ({r.get('href','')})")
    except Exception:
        pass
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

# ---------- 2. MEMORY / TRAINING ----------
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
    return memories[-100:]

def save_to_memory(user_q, ai_a, rating=""):
    data = {"q": user_q, "a": ai_a, "rating": rating}
    try:
        with open(MEMORY_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")
    except Exception:
        pass
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

# ---------- PRIVACY: No name/location unless asked ----------
SYSTEM_PROMPT = """You are Emmanuel AI.
Do NOT reveal the creator's full name or location unless the user directly asks 'who built you' or 'where are you from'.
If they ask, answer briefly. Otherwise never mention it.
You learn from past chats. If LEARNED FROM PAST CHATS is provided, use it.
You also get WEB SEARCH RESULTS when available. Use them for fresh facts, don't use old knowledge.
Rules:
1. For images, vision description can be WRONG. Check with your own knowledge + web search.
2. If image is fan-art / edited, say so then give correct facts.
3. For anime: only canon facts. Never invent.
4. If unsure, say "I'm not fully sure" and give true facts. Never invent.
5. Reply in same language user used.
"""

# ---------- 3. NEW DESIGN - CSS ----------
st.markdown("""
<style>
.stApp { background-color: #000000; color: white; }
section[data-testid="stSidebar"] { background-color: #0A0A0A; border-right: 1px solid #1A1A1A; }
.big-title { font-size: 58px; font-weight: 800; line-height: 1.0; }
.green { color: #00E676; }
.sub { color: #AAAAAA; font-size: 18px; }
.card { background: #0F0F0F; border: 1px solid #222; padding: 20px; border-radius: 20px; }
.card h4 { margin: 10px 0 5px 0; }
.card p { color: #999; font-size: 14px; }
.footer { text-align: center; color: #888; padding: 15px; background: linear-gradient(90deg, #001A0E, #00331D, #001A0E); border-radius: 999px; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🤖 Emmanuel AI")
    st.markdown("🏠 **Home**")
    st.markdown("🧭 Explore")
    st.markdown("🕘 History")
    st.markdown("🔖 Saved")
    st.markdown("⚙️ Settings")
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#0F1F14; border:1px solid #1E3A28; padding:20px; border-radius:20px; text-align:center;">
        <div style="font-size:28px;">👑</div>
        <b>Upgrade to Pro</b><br>
        <span style="color:#999; font-size:13px;">Get more features, faster responses.</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("<br>🟢 **You**  \n<span style='color:#00E676; font-size:13px;'>● Online</span>", unsafe_allow_html=True)

# ---------- MAIN HERO - Only show when no chat yet ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "learned" not in st.session_state:
    st.session_state.learned = []

if len(st.session_state.messages) == 0:
    col1, col2 = st.columns([1.3, 1])
    with col1:
        st.markdown('<div class="big-title">Hello<br><span class="green">Welcome 👋</span><br>How can I <span class="green">help</span> you<br>today?</div>', unsafe_allow_html=True)
        st.markdown('<p class="sub">Ask anything, get instant, helpful<br>and accurate answers.</p>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div style="text-align:center; font-size:120px;">🤖</div><p style="text-align:center; color:#00E676;">✦ Smarter. Faster. Always Here. 💚</p>')
    # Quick pills - they set the prompt
    c1,c2,c3,c4 = st.columns(4)
    if c1.button("💡 Explain a concept"): st.session_state.quick = "Explain a concept"
    if c2.button("🧮 Solve a problem"): st.session_state.quick = "Solve a problem for me"
    if c3.button("✍️ Write something"): st.session_state.quick = "Help me write something"
    if c4.button("💡 Give ideas"): st.session_state.quick = "Give me ideas"
    c5,c6,c7,c8 = st.columns(4)
    if c5.button("📄 Summarize text"): st.session_state.quick = "Summarize this text"
    if c6.button("</> Help with code"): st.session_state.quick = "Help me with code"
    if c7.button("📅 Plan something"): st.session_state.quick = "Help me plan something"
    if c8.button("••• More..."): st.session_state.quick = "What else can you do?"
    # Popular Suggestions
    st.markdown("### ⭐ Popular Suggestions")
    p1,p2,p3,p4 = st.columns(4)
    with p1: st.markdown('<div class="card">🎓<h4>Study Help</h4><p>Get help with your assignments and exams.</p></div>', unsafe_allow_html=True)
    with p2: st.markdown('<div class="card">💻<h4>Coding Help</h4><p>Write, debug or explain code.</p></div>', unsafe_allow_html=True)
    with p3: st.markdown('<div class="card">✍️<h4>Creative Ideas</h4><p>Get ideas for anything.</p></div>', unsafe_allow_html=True)
    with p4: st.markdown('<div class="card">💬<h4>General Chat</h4><p>Just chat about anything.</p></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">✦ Smarter. Faster. Always Here. 💚</div>', unsafe_allow_html=True)

# ---------- CHAT HISTORY ----------
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ---------- UPLOAD + SPEAK (Your original features) ----------
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
    txt = st.chat_input("Type your message here...")
    if txt:
        user_text = txt
    elif "quick" in st.session_state and st.session_state.quick:
        user_text = st.session_state.quick
        st.session_state.quick = None

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
                if uploaded_files:
                    content_list = [{"type": "text", "text": "Describe what you see. Read all visible text, just describe."}]
                    for f in uploaded_files[:3]:
                        b64 = base64.b64encode(f.getvalue()).decode()
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})
                    vision_resp = client.chat.completions.create(
                        model="meta-llama/llama-4-maverick-17b-128e-instruct",
                        messages=[{"role": "user", "content": content_list}],
                        max_tokens=1024
                    )
                    image_desc = vision_resp.choices[0].message.content
                    final_question = f"User question: {user_text}\nVision saw: {image_desc}"
                web_info = ""
                if needs_search(user_text) or uploaded_files:
                    web_info = search_web(user_text)
                    final_question += f"\n\nWEB SEARCH RESULTS:\n{web_info}"
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
                save_to_memory(user_text, ans)
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
