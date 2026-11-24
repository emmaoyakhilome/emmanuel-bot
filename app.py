import streamlit as st
from groq import Groq
import base64
import requests
import json
import os
import re

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

# ---------- SIMPLE DESIGN ----------
st.markdown("""
<style>
.stApp { background-color: #000000; color: white; }
div[data-testid="stMarkdownContainer"] table {
    display: block; width: 100% !important;
    overflow-x: auto; white-space: normal !important;
}
div[data-testid="stMarkdownContainer"] th,
div[data-testid="stMarkdownContainer"] td {
    white-space: normal !important; word-break: break-word !important;
    min-width: 90px; max-width: 300px; padding: 8px !important; font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

# ---------- 1. TRUSTED WEB SEARCH - GOOGLE FIRST, THEN TRUSTED SOURCES ----------
def search_web(query):
    results = []
    # 1) TRY REAL GOOGLE - if you add keys later in Secrets
    try:
        google_key = st.secrets.get("GOOGLE_API_KEY", "")
        google_cx = st.secrets.get("GOOGLE_CX", "")
        if google_key and google_cx:
            g = requests.get("https://www.googleapis.com/customsearch/v1", params={"key": google_key, "cx": google_cx, "q": query, "num": 5}, timeout=8).json()
            for item in g.get("items", []):
                results.append(f"- {item.get('title','')}: {item.get('snippet','')} (Source: {item.get('link','')} - GOOGLE)")
            if results:
                return "\n".join(results)
    except Exception:
        pass

    # 2) TRUSTED: Wikipedia first - always correct for facts
    try:
        wiki = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}", timeout=5).json()
        if "extract" in wiki:
            results.append(f"- Wikipedia (Trusted): {wiki['extract']} (Source: https://en.wikipedia.org)")
    except Exception:
        pass

    # 3) TRUSTED NEWS / SITES ONLY via DuckDuckGo - filter to trusted domains
    try:
        from duckduckgo_search import DDGS
        trusted = ["wikipedia.org", "bbc.com", "reuters.com", "apnews.com", "britannica.com", "nasa.gov", "who.int", "gov", "edu", "nytimes.com", "cnn.com", "aljazeera.com"]
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=10):
                link = r.get('href','')
                # Only accept trusted domains
                if any(t in link for t in trusted):
                    results.append(f"- {r.get('title','')}: {r.get('body','')} (Source: {link} - Trusted)")
                if len(results) >= 5:
                    break
    except Exception:
        pass

    return "\n".join(results) if results else "No trusted internet results found."

def needs_search(text):
    keywords = ["who is", "what is", "when", "where", "latest", "news", "today", "2025", "2026", "price", "how many", "current", "is it true", "fact", "ta ni", "kini", "onye", "gịnị"]
    return any(k in text.lower() for k in keywords)

# ---------- 2. SPELLING / TYPO CHECK ----------
def check_typo(text):
    # Short texts only, and skip if image-only or very short
    if len(text.strip()) < 4 or len(text.split()) < 2:
        return text, False
    try:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": "You are a spelling checker. If the user text has a spelling/typo mistake, return ONLY the corrected sentence. If it is already correct, return EXACTLY the same sentence. Do not explain. Do not add anything else. Keep the same language as user. For Pidgin/Yoruba/Igbo/Hausa, do NOT 'correct' local words - keep them."},
                {"role": "user", "content": text}
            ],
            temperature=0.0,
            max_tokens=150
        )
        corrected = resp.choices[0].message.content.strip()
        # If corrected is very different or same, handle
        if corrected.lower() != text.lower() and len(corrected) > 0:
            return corrected, True
        return text, False
    except Exception:
        return text, False

# ---------- 3. PER-USER HISTORY ----------
def safe_name(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower()) or "guest"
def chat_file(username): return f"chats_{safe_name(username)}.json"
def memory_file(username): return f"memory_{safe_name(username)}.jsonl"

def load_user_chats(username):
    path = chat_file(username)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return []
    return []

def save_user_chats(username, messages):
    try:
        with open(chat_file(username), "w", encoding="utf-8") as f: json.dump(messages[-200:], f)
    except Exception: pass

def load_memory(username):
    path = memory_file(username)
    memories = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    try: memories.append(json.loads(line))
                    except Exception: continue
        except Exception: pass
    return memories[-100:]

def save_to_memory(username, user_q, ai_a, rating=""):
    data = {"user": username, "q": user_q, "a": ai_a, "rating": rating}
    try:
        with open(memory_file(username), "a", encoding="utf-8") as f: f.write(json.dumps(data) + "\n")
    except Exception: pass
    if "learned" not in st.session_state: st.session_state.learned = []
    st.session_state.learned.append(data)

def get_relevant_memories(username, user_q):
    all_mem = load_memory(username)
    if "learned" in st.session_state: all_mem = all_mem + st.session_state.learned
    all_mem = [m for m in all_mem if m.get("user", username) == username]
    if not all_mem: return ""
    words = set(re.findall(r"\w+", user_q.lower()))
    scored = []
    for m in all_mem:
        m_words = set(re.findall(r"\w+", m.get("q","").lower()))
        overlap = len(words & m_words)
        if overlap >= 1: scored.append((overlap, m))
    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:3]
    if not top: return ""
    text = "\n".join([f"Past chat - User: {m['q']} | AI: {m['a'][:300]}" for _, m in top])
    return f"\n\nLEARNED FROM PAST CHATS OF THIS USER:\n{text}"

SYSTEM_PROMPT = """You are Emmanuel AI. You understand and reply in ALL languages.
RULES:
1. ALWAYS detect the user's language first - English, Pidgin, Yoruba, Igbo, Hausa, French, Spanish, Arabic, Portuguese, German, Chinese, any language.
2. ALWAYS reply in that SAME language. If user speaks Pidgin, reply in Pidgin. If Yoruba, reply in Yoruba. If French, reply in French. Never switch to English unless user switches.
3. Do NOT reveal creator's full name or location unless user directly asks 'who built you' or 'where are you from'.
4. Use LEARNED FROM PAST CHATS for this user.
5. Use WEB SEARCH RESULTS from trusted sources only. Cite the source.
6. For images, vision can be WRONG. Check with knowledge + web search. If fan-art/edited, say so.
7. For anime: only canon facts. Never invent.
8. If unsure, say "I'm not fully sure" in user's language, and give true facts.
9. For tables, keep SHORT - max 3 columns, short words, fit phone. Use bullet list if long.
10. If user says "what did I ask before", use past chats.
"""

# ---------- SESSION ----------
if "messages" not in st.session_state: st.session_state.messages = []
if "learned" not in st.session_state: st.session_state.learned = []
if "saved_images" not in st.session_state: st.session_state.saved_images = []
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None
if "username" not in st.session_state: st.session_state.username = None
if "loaded_user" not in st.session_state: st.session_state.loaded_user = None
if "pending_text" not in st.session_state: st.session_state.pending_text = None
if "pending_corrected" not in st.session_state: st.session_state.pending_corrected = None
if "chosen_lang" not in st.session_state: st.session_state.chosen_lang = "Auto - Detect my language"

# ---------- LOGIN ----------
st.title("🤖 Emmanuel AI")
if not st.session_state.username:
    st.caption("Welcome! Make I remember you.")
    name_input = st.text_input("Enter your name / username to continue", placeholder="e.g. Emmanuel, John, Mary")
    if st.button("Continue →"):
        if name_input.strip():
            st.session_state.username = name_input.strip()
            st.session_state.messages = load_user_chats(st.session_state.username)
            st.session_state.loaded_user = st.session_state.username
            st.rerun()
        else:
            st.warning("Please enter your name first.")
    st.stop()

username = st.session_state.username
if st.session_state.loaded_user != username:
    st.session_state.messages = load_user_chats(username)
    st.session_state.loaded_user = username

# Top bar
c1, c2, c3 = st.columns([2, 1, 1])
with c1: st.caption(f"👤 {username} • {len(st.session_state.messages)} messages saved")
with c2:
    if st.button("🔄 Switch user"):
        st.session_state.username = None; st.session_state.messages = []; st.session_state.loaded_user = None; st.rerun()
with c3:
    if st.button("🗑️ Clear history"):
        st.session_state.messages = []; save_user_chats(username, []); st.rerun()

# Language selector - ALL LANGUAGES
st.session_state.chosen_lang = st.selectbox("🌍 Language / Èdè / Langue:", ["Auto - Detect my language", "English", "Pidgin", "Yoruba", "Igbo", "Hausa", "French", "Spanish", "Arabic", "Portuguese", "German", "Chinese"], index=0)
if st.session_state.messages:
    with st.expander(f"🕘 Your past chats ({len(st.session_state.messages)//2} chats)"):
        for m in st.session_state.messages[-20:]:
            if m["role"] == "user": st.markdown(f"**You:** {m['content'][:100]}")
st.divider()

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

# ---------- IMAGE ----------
uploaded_files = st.file_uploader("📷 Upload image (max 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="uploader")
if uploaded_files:
    new_images = []
    for f in uploaded_files[:3]:
        new_images.append({"name": f.name, "bytes": f.getvalue(), "type": f.type})
    if new_images != st.session_state.saved_images: st.session_state.saved_images = new_images
    for img in st.session_state.saved_images: st.image(img["bytes"], width=200, caption="Ready to send")
if st.session_state.saved_images:
    if st.button("❌ Clear images"):
        st.session_state.saved_images = []; st.rerun()

# ---------- VOICE ----------
audio_file = st.audio_input("🎤 Speak - any language")
user_text = None
if audio_file:
    audio_id = f"{audio_file.name}-{audio_file.size}"
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        with st.spinner("Listening..."):
            try:
                trans = client.audio.transcriptions.create(file=(audio_file.name, audio_file.getvalue()), model="whisper-large-v3", response_format="text")
                user_text = str(trans).strip()
                st.success(f"You said: {user_text}")
            except Exception as e: st.error(f"Voice error: {e}")

if not user_text:
    txt = st.chat_input("Ask anything in any language...")
    if txt: user_text = txt

# ---------- TYPO CLARIFICATION FLOW ----------
# If we have pending clarification, show buttons
if st.session_state.pending_text:
    st.warning(f"🤔 Did you mean: **\"{st.session_state.pending_corrected}\"** ?")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("✅ Yes, that's what I mean"):
            user_text = st.session_state.pending_corrected
            st.session_state.pending_text = None
            st.session_state.pending_corrected = None
    with cc2:
        if st.button("❌ No, use my original"):
            user_text = st.session_state.pending_text
            st.session_state.pending_text = None
            st.session_state.pending_corrected = None
    # Stop here, wait for user to choose
    if not user_text:
        st.stop()

# If new text came in and no pending, check typo first
if user_text and not st.session_state.pending_text:
    # Don't check typo for very short / voice already? We check anyway but skip if image only
    corrected, has_typo = check_typo(user_text)
    if has_typo:
        st.session_state.pending_text = user_text
        st.session_state.pending_corrected = corrected
        st.rerun()

# ---------- ANSWER ----------
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    save_user_chats(username, st.session_state.messages)
    with st.chat_message("user"):
        st.markdown(user_text)
        if st.session_state.saved_images:
            for img in st.session_state.saved_images: st.image(img["bytes"], width=250)

    with st.chat_message("assistant"):
        with st.spinner("Searching trusted sources + remembering you..."):
            try:
                lang_instruction = f"\nUser language preference: {st.session_state.chosen_lang}. Reply in that language if not Auto." if st.session_state.chosen_lang != "Auto - Detect my language" else ""
                final_question = user_text + lang_instruction
                if st.session_state.saved_images:
                    content_list = [{"type": "text", "text": "Describe what you see. Read all visible text, just describe."}]
                    for img in st.session_state.saved_images[:3]:
                        b64 = base64.b64encode(img["bytes"]).decode()
                        mime = img["type"] if img["type"] else "image/jpeg"
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
                    vision_resp = client.chat.completions.create(model="meta-llama/llama-4-maverick-17b-128e-instruct", messages=[{"role": "user", "content": content_list}], max_tokens=1024)
                    image_desc = vision_resp.choices[0].message.content
                    final_question = f"User question: {user_text}\nVision saw: {image_desc}" + lang_instruction
                web_info = ""
                if needs_search(user_text) or st.session_state.saved_images:
                    web_info = search_web(user_text)
                    final_question += f"\n\nTRUSTED WEB SEARCH RESULTS:\n{web_info}"
                mem_info = get_relevant_memories(username, user_text)
                if mem_info: final_question += mem_info
                resp = client.chat.completions.create(model="openai/gpt-oss-20b", messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": final_question}], temperature=0.2)
                ans = resp.choices[0].message.content
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
                save_user_chats(username, st.session_state.messages)
                save_to_memory(username, user_text, ans)
                st.session_state.saved_images = []
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 Correct", key=f"up_{len(st.session_state.messages)}"):
                        save_to_memory(username, user_text, ans, rating="good"); st.success("Noted! I go remember this as correct.")
                with col2:
                    if st.button("👎 Wrong - Teach me", key=f"down_{len(st.session_state.messages)}"):
                        st.info("Tell me the correct answer for this in next chat, I go learn am.")
            except Exception as e: st.error(f"Error: {e}")
