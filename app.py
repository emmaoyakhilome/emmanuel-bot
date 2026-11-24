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

# ---------- SLANG + SHORT FORM DICTIONARY - MAKE AI FAMILIAR LIKE ME ----------
SLANG_MAP = {
    # Naija / Pidgin greetings
    "hwf": "how far", "hwf na": "how far na", "hwd": "how far dey go",
    "how far na": "how far na", "wetin dey": "what is happening", "wetin": "what",
    "how e be": "how is it", "how e dey go": "how is it going",
    "wey": "where", "weytin": "what", "abi": "right?",
    "abeg": "please", "biko": "please", "ehn": "huh", "o": "",
    "na wa": "wow / unbelievable", "na wa o": "wow",
    "no wahala": "no problem", "wahala": "trouble / problem",
    "japa": "travel abroad / run away", "sapa": "broke / no money",
    "cruise": "fun / joke", "yarn": "talk / gist", "gist": "gossip / talk",
    "gbam": "exactly / bang", "e choke": "it is amazing / too much",
    "shey": "is it / right?", "shebi": "isn't it",
    "oga": "boss / sir", "boss": "boss", "my guy": "my friend",
    "chop": "eat", "waka": "walk / go", "comot": "go out",
    "na": "", "dey": "is", "go": "will",
    # Gen Z / Internet short forms
    "wyd": "what are you doing", "wya": "where are you",
    "wbu": "what about you", "wuu2": "what are you up to",
    "idk": "I don't know", "ikr": "I know right", "tbh": "to be honest",
    "ngl": "not gonna lie", "lol": "laughing", "lmao": "laughing hard",
    "omg": "oh my God", "omg": "oh my God", "asap": "as soon as possible",
    "brb": "be right back", "btw": "by the way", "fyi": "for your information",
    "imo": "in my opinion", "imho": "in my humble opinion",
    "nvm": "never mind", "ty": "thank you", "thx": "thanks",
    "pls": "please", "plz": "please", "u": "you", "ur": "your",
    "y": "why", "bcos": "because", "cos": "because", "cuz": "because",
    "wot": "what", "wat": "what", "wen": "when", "whr": "where",
    "gm": "good morning", "gn": "good night", "gd": "good",
    "fr": "for real", "fr fr": "for real for real", "on god": "I swear",
    "bet": "okay / deal", "cap": "lie", "no cap": "no lie",
    "slay": "you did great", "vibe": "feeling", "vibes": "feelings",
    "sus": "suspicious", "rizz": "charm", "bussin": "very good",
    "lit": "amazing / fun", "fire": "amazing", "goat": "greatest of all time",
    "w": "win / good", "l": "loss / bad",
    "fomo": "fear of missing out", "yolo": "you only live once",
    "smh": "shaking my head", "istg": "I swear to God",
    "ofc": "of course", "obv": "obviously", "rn": "right now",
    "tmr": "tomorrow", "tmo": "tomorrow", "2moro": "tomorrow",
    "2day": "today", "2nite": "tonight", "gr8": "great",
    "luv": "love", "bae": "boyfriend / girlfriend / love",
    "bestie": "best friend", "fam": "family / friend",
    "bro": "brother / friend", "sis": "sister / friend",
    "dunno": "don't know", "gonna": "going to", "wanna": "want to",
    "gotta": "got to", "kinda": "kind of", "sorta": "sort of",
    "yea": "yeah", "yeah": "yes", "yup": "yes", "nah": "no",
    "ok": "okay", "kk": "okay", "k": "okay",
    "hbd": "happy birthday", "hny": "happy new year",
    "rip": "rest in peace", "f": "respect",
    # School / Nigeria specific
    "redeemer's": "Redeemer's University", "rdu": "Redeemer's University",
    "zip": "Zip", "unilag": "University of Lagos", "oau": "Obafemi Awolowo University",
    "ui": "University of Ibadan", "lasu": "Lagos State University",
}

def expand_slang(text):
    low = text.lower().strip()
    # Direct match first - e.g. "hwf na" -> "how far na"
    if low in SLANG_MAP:
        return SLANG_MAP[low]
    # Replace slang words inside sentence
    words = re.findall(r"\w+|[^\w\s]", low)
    out = []
    for w in words:
        if w in SLANG_MAP and SLANG_MAP[w] != "":
            out.append(SLANG_MAP[w])
        else:
            out.append(w)
    expanded = " ".join(out)
    expanded = re.sub(r"\s+([?.!,])", r"\1", expanded)
    return expanded

def is_slang_only(text):
    return text.lower().strip() in SLANG_MAP or text.lower().strip() in ["hwf", "hwf na", "hwd", "wyd", "wbu", "how far", "wetin dey"]

# ---------- TRUSTED WEB SEARCH ----------
def search_web(query):
    results = []
    try:
        google_key = st.secrets.get("GOOGLE_API_KEY", "")
        google_cx = st.secrets.get("GOOGLE_CX", "")
        if google_key and google_cx:
            g = requests.get("https://www.googleapis.com/customsearch/v1", params={"key": google_key, "cx": google_cx, "q": query, "num": 5}, timeout=8).json()
            for item in g.get("items", []):
                results.append(f"- {item.get('title','')}: {item.get('snippet','')} (Source: {item.get('link','')} - GOOGLE)")
            if results: return "\n".join(results)
    except Exception: pass
    try:
        wiki = requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{query}", timeout=5).json()
        if "extract" in wiki:
            results.append(f"- Wikipedia (Trusted): {wiki['extract']} (Source: https://en.wikipedia.org)")
    except Exception: pass
    try:
        from duckduckgo_search import DDGS
        trusted = ["wikipedia.org", "bbc.com", "reuters.com", "apnews.com", "britannica.com", "nasa.gov", "who.int", "gov", "edu", "nytimes.com", "cnn.com", "aljazeera.com"]
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=10):
                link = r.get('href','')
                if any(t in link for t in trusted):
                    results.append(f"- {r.get('title','')}: {r.get('body','')} (Source: {link} - Trusted)")
                if len(results) >= 5: break
    except Exception: pass
    return "\n".join(results) if results else "No trusted internet results found."

def needs_search(text):
    keywords = ["who is", "what is", "when", "where", "latest", "news", "today", "2025", "2026", "price", "how many", "current", "is it true", "fact"]
    return any(k in text.lower() for k in keywords)

# ---------- SPELLING - SKIP SLANG ----------
def check_typo(text):
    if is_slang_only(text):
        return text, False
    if len(text.strip()) < 4 or len(text.split()) < 2:
        return text, False
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a spelling checker. If user text has spelling mistake, return ONLY corrected sentence. If correct, return EXACTLY same sentence. Do NOT correct slang, Pidgin, Yoruba, Igbo, Hausa, Gen Z short forms like hwf, wyd, idk, lol, tbh, ngl, abeg, wahala. Keep them as is. Do not explain."},
                {"role": "user", "content": text}
            ],
            temperature=0.0, max_tokens=150
        )
        corrected = resp.choices[0].message.content.strip()
        if corrected.lower() != text.lower() and len(corrected) > 0:
            return corrected, True
        return text, False
    except Exception:
        return text, False

# ---------- SAFE CHAT - FIX 400 ERROR + FALLBACK MODELS ----------
def safe_chat(messages, max_tokens=1024):
    # Try stable models in order, no tools, so no 400 tool error
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
    last_err = None
    for model in models:
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            continue
    raise last_err

def safe_vision(content_list):
    # FIX 404 - try working vision models in order
    vision_models = ["llama-3.2-11b-vision-preview", "llama-3.2-90b-vision-preview"]
    last_err = None
    for model in vision_models:
        try:
            resp = client.chat.completions.create(model=model, messages=[{"role": "user", "content": content_list}], max_tokens=1024, temperature=0.2)
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            continue
    # If vision fails, don't show error code, return friendly description
    return "I fit see the image but my vision dey have wahala now. Please describe wetin dey for the image, or try again."

# ---------- PER-USER HISTORY ----------
def safe_name(name): return re.sub(r"[^a-zA-Z0-9_-]", "_", name.strip().lower()) or "guest"
def chat_file(u): return f"chats_{safe_name(u)}.json"
def memory_file(u): return f"memory_{safe_name(u)}.jsonl"
def load_user_chats(u):
    if os.path.exists(chat_file(u)):
        try:
            with open(chat_file(u), "r", encoding="utf-8") as f: return json.load(f)
        except Exception: return []
    return []
def save_user_chats(u, messages):
    try:
        with open(chat_file(u), "w", encoding="utf-8") as f: json.dump(messages[-200:], f)
    except Exception: pass
def load_memory(u):
    memories = []
    if os.path.exists(memory_file(u)):
        try:
            with open(memory_file(u), "r", encoding="utf-8") as f:
                for line in f:
                    try: memories.append(json.loads(line))
                    except Exception: continue
        except Exception: pass
    return memories[-100:]
def save_to_memory(u, user_q, ai_a, rating=""):
    data = {"user": u, "q": user_q, "a": ai_a, "rating": rating}
    try:
        with open(memory_file(u), "a", encoding="utf-8") as f: f.write(json.dumps(data) + "\n")
    except Exception: pass
    if "learned" not in st.session_state: st.session_state.learned = []
    st.session_state.learned.append(data)
def get_relevant_memories(u, user_q):
    all_mem = load_memory(u)
    if "learned" in st.session_state: all_mem = all_mem + st.session_state.learned
    all_mem = [m for m in all_mem if m.get("user", u) == u]
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

SYSTEM_PROMPT = """You are Emmanuel AI. You are VERY familiar with Nigerian slang, Pidgin, Gen Z slang, and all short forms - like a real Nigerian friend.

SLANG YOU MUST KNOW:
- hwf / hwf na / hwd = How far, greet person warmly. Reply like "I dey o, hwf na? How your side?"
- wyd = what are you doing, wbu = what about you, wya = where are you
- idk, ikr, tbh, ngl, lol, lmao, omg, asap, brb, btw, fyi, imo, nvm
- abeg, wahala, no wahala, japa, sapa, cruise, yarn, gist, gbam, e choke, shey, na wa, oga, my guy
- u, ur, pls, thx, coz, bcos, wot, wat, gm, gn, fr, no cap, bet, slay, vibe, sus, rizz, lit, fire, goat
- If user uses slang/short form, REPLY IN SAME STYLE. Don't be too formal. Be friendly like Meta AI.
- If user types "hwf", NEVER say "I don't understand". Answer "I dey o, hwf na?"
- If user types "wyd", answer what you are doing and ask them.
- If user types "who is" with a name, give real facts.
- For images, vision can be WRONG. Check with knowledge + web search. If fan-art, say so.
- For anime: only canon facts. Never invent.
- If unsure, say "I'm not fully sure" in user's language, give true facts.
- Reply in SAME language user used - English, Pidgin, Yoruba, Igbo, Hausa, French, Spanish, any language.
- For tables, keep SHORT - max 3 columns, fit phone.
- NEVER show error codes. NEVER say "Error code 400 / 404". If something fails, say friendly "Network wahala small, try again".
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
        else: st.warning("Please enter your name first.")
    st.stop()

username = st.session_state.username
if st.session_state.loaded_user != username:
    st.session_state.messages = load_user_chats(username)
    st.session_state.loaded_user = username

c1, c2, c3 = st.columns([2, 1, 1])
with c1: st.caption(f"👤 {username} • {len(st.session_state.messages)} messages saved")
with c2:
    if st.button("🔄 Switch user"):
        st.session_state.username = None; st.session_state.messages = []; st.session_state.loaded_user = None; st.rerun()
with c3:
    if st.button("🗑️ Clear history"):
        st.session_state.messages = []; save_user_chats(username, []); st.rerun()

st.session_state.chosen_lang = st.selectbox("🌍 Language:", ["Auto - Detect my language", "English", "Pidgin", "Yoruba", "Igbo", "Hausa", "French", "Spanish", "Arabic", "Portuguese", "German", "Chinese"], index=0)
if st.session_state.messages:
    with st.expander(f"🕘 Your past chats ({len(st.session_state.messages)//2} chats)"):
        for m in st.session_state.messages[-20:]:
            if m["role"] == "user": st.markdown(f"**You:** {m['content'][:100]}")
st.divider()

for m in st.session_state.messages:
    with st.chat_message(m["role"]): st.markdown(m["content"])

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
            except Exception:
                st.error("Voice wahala small, abeg try again - speak clear and close to phone.")

if not user_text:
    txt = st.chat_input("Ask anything - slang, pidgin, any language...")
    if txt: user_text = txt

# TYPO FLOW - skip if slang
if st.session_state.pending_text:
    st.warning(f"🤔 Did you mean: **\"{st.session_state.pending_corrected}\"** ?")
    cc1, cc2 = st.columns(2)
    with cc1:
        if st.button("✅ Yes, that's what I mean"):
            user_text = st.session_state.pending_corrected
            st.session_state.pending_text = None; st.session_state.pending_corrected = None
    with cc2:
        if st.button("❌ No, use my original"):
            user_text = st.session_state.pending_text
            st.session_state.pending_text = None; st.session_state.pending_corrected = None
    if not user_text: st.stop()

if user_text and not st.session_state.pending_text:
    if not is_slang_only(user_text):
        corrected, has_typo = check_typo(user_text)
        if has_typo:
            st.session_state.pending_text = user_text
            st.session_state.pending_corrected = corrected
            st.rerun()

if user_text:
    # Expand slang for AI to understand better, but keep original for display
    expanded = expand_slang(user_text)
    st.session_state.messages.append({"role": "user", "content": user_text})
    save_user_chats(username, st.session_state.messages)
    with st.chat_message("user"):
        st.markdown(user_text)
        if st.session_state.saved_images:
            for img in st.session_state.saved_images: st.image(img["bytes"], width=250)

    with st.chat_message("assistant"):
        with st.spinner("Searching trusted sources + remembering you..."):
            try:
                lang_instruction = f"\nUser language preference: {st.session_state.chosen_lang}." if st.session_state.chosen_lang != "Auto - Detect my language" else ""
                # Use expanded version for understanding, original for style
                final_question = f"User said (original): {user_text}\nUser said (expanded slang): {expanded}" + lang_instruction
                if st.session_state.saved_images:
                    content_list = [{"type": "text", "text": "Describe what you see. Read all visible text, just describe."}]
                    for img in st.session_state.saved_images[:3]:
                        b64 = base64.b64encode(img["bytes"]).decode()
                        mime = img["type"] if img["type"] else "image/jpeg"
                        content_list.append({"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}})
                    image_desc = safe_vision(content_list)
                    final_question = f"User question: {user_text} (expanded: {expanded})\nVision saw: {image_desc}" + lang_instruction
                web_info = ""
                if needs_search(expanded) or st.session_state.saved_images:
                    web_info = search_web(expanded)
                    final_question += f"\n\nTRUSTED WEB SEARCH RESULTS:\n{web_info}"
                mem_info = get_relevant_memories(username, expanded)
                if mem_info: final_question += mem_info
                ans = safe_chat([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": final_question}])
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
            except Exception:
                # NEVER show raw error code to user
                st.error("Network wahala small, abeg try again. If e continue, wait 1 min and press Send again.")
