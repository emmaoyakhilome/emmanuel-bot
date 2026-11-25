import asyncio
import base64
import hashlib
import hmac
import io
import json
import os
import re
import secrets
from datetime import datetime
from urllib.parse import urlparse

import requests
import streamlit as st
from groq import Groq
from PIL import Image, ImageOps

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")

# =====================================================================
# CONFIG  (model names change often - check Groq / Google model lists)
# =====================================================================
CHAT_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "openai/gpt-oss-20b"]
GROQ_VISION_MODELS = [
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
]
GEMINI_MODEL = "gemini-2.5-flash"
WHISPER_MODEL = "whisper-large-v3-turbo"  # use "whisper-large-v3" for max accuracy

AUTO = "Auto - Detect my language"
# language -> text-to-speech voice (edge-tts)
LANGUAGES = {
    AUTO: "en-NG-EzinneNeural",
    "English": "en-NG-EzinneNeural",
    "Pidgin": "en-NG-AbeoNeural",
    "Yoruba": "en-NG-EzinneNeural",
    "Igbo": "en-NG-EzinneNeural",
    "Hausa": "en-NG-EzinneNeural",
    "French": "fr-FR-DeniseNeural",
    "Spanish": "es-ES-ElviraNeural",
    "Arabic": "ar-SA-ZariyahNeural",
    "Portuguese": "pt-BR-FranciscaNeural",
    "German": "de-DE-KatjaNeural",
    "Chinese": "zh-CN-XiaoxiaoNeural",
}

DATA_DIR = "data"  # add "data/" to .gitignore - it holds private chats
USERS_FILE = os.path.join(DATA_DIR, "users.json")
os.makedirs(DATA_DIR, exist_ok=True)

FRIENDLY_ERROR = "Network wahala small 😅 - abeg try again. If e continue, wait small and send again."
DEBUG = False  # switched on from the sidebar

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.markdown("""
<style>
.stApp { background-color: #000000; color: white; }
div[data-testid="stMarkdownContainer"] table {
    display: block; width: 100% !important; overflow-x: auto; white-space: normal !important;
}
div[data-testid="stMarkdownContainer"] th,
div[data-testid="stMarkdownContainer"] td {
    white-space: normal !important; word-break: break-word !important;
    min-width: 90px; max-width: 300px; padding: 8px !important; font-size: 14px;
}
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are Emmanuel AI, a friendly and smart assistant who is very familiar with Nigerian Pidgin, Nigerian English, Yoruba, Igbo, Hausa and Gen Z slang.
- Slang you know: hwf = how far, wyd = what are you doing, wbu = what about you, abeg = please, wahala = trouble, japa = relocate abroad, sapa = being broke, gist/yarn = chat, gbam = exactly, e choke = amazing, shey = is it, na wa = wow, oga = boss, tbh, ngl, fr, no cap, rizz, sus.
- Identity: You were created by Emmanuel in 2026. You are NOT ChatGPT or GPT-4 acreator, say you are Emmanuel AI, a chatbot built on top of AI models from Meta (Llama) and Google (Gemini). Never claim a different creator, version, or release year you were not made by OpenAI. If asked about your model or release year.
- Reply in the SAME language and style the user uses. If they use Pidgin or slang, answer casually in the same way. Don't be stiff.
- Never say you don't understand common slang like "hwf".
- Never repeat a greeting you already gave. If the user answers your greeting, move the conversation forward.
- Use the chat history. Don't start fresh every time.
- Images: describe what you actually see and read any text in it. Only name a character, show or product if you are confident, and say if it might be fan-art. Never identify real people from their faces.
- For anime, games and shows, stick to canon facts. Never invent.
- If web search results are provided, use them for current facts and mention the source name. If unsure, say "I'm not fully sure" in the user's language.
- Keep tables short (max 3 columns) so they fit a phone.
- Never show error codes or technical errors to the user."""


def report(msg, err):
    """Log errors to the console; show them in the sidebar when Debug is on."""
    print(f"{msg}: {err}")
    if DEBUG:
        st.sidebar.error(f"{msg}: {err}")


# =====================================================================
# STORAGE  (local JSON files - these reset on Streamlit Cloud restarts.
# For real persistence, swap these helpers for Supabase / Firebase.)
# =====================================================================
def safe_name(name):
    return re.sub(r"[^a-z0-9_-]", "_", name.strip().lower()) or "guest"


def user_path(kind, user, ext):
    return os.path.join(DATA_DIR, f"{kind}_{safe_name(user)}.{ext}")


def read_json(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def write_json(path, obj):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)
    except Exception as e:
        report("write_json", e)


def hash_pin(pin, salt_hex):
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), bytes.fromhex(salt_hex), 100_000).hex()


def login(user, pin):
    """New name -> creates the account. Existing name -> PIN must match."""
    users = read_json(USERS_FILE, {})
    key = safe_name(user)
    if key in users:
        ok = hmac.compare_digest(users[key]["hash"], hash_pin(pin, users[key]["salt"]))
        return ok, "" if ok else "Wrong PIN for this name."
    salt = secrets.token_hex(16)
    users[key] = {"salt": salt, "hash": hash_pin(pin, salt)}
    write_json(USERS_FILE, users)
    return True, ""


def save_chats(user, messages):
    write_json(user_path("chats", user, "json"), messages[-200:])


# =====================================================================
# MEMORY  (only answers the user approved or corrected are remembered)
# =====================================================================
STOP = set("the an is are was were to of and or in on at for with what who how why when where "
           "does did you your me my it this that can be have has not yes".split())


def keywords(text):
    return {w for w in re.findall(r"\w+", text.lower()) if len(w) > 2 and w not in STOP}


def save_memory(user, q, a, rating):
    try:
        with open(user_path("memory", user, "jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps({"q": q, "a": a, "rating": rating}) + "\n")
    except Exception as e:
        report("save_memory", e)


def relevant_memories(user, question):
    kw = keywords(question)
    path = user_path("memory", user, "jsonl")
    if not kw or not os.path.exists(path):
        return ""
    need = min(2, len(kw))
    scored = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                m = json.loads(line)
            except Exception:
                continue
            overlap = len(kw & keywords(m.get("q", "")))
            if overlap >= need:
                scored.append((overlap, m))
    scored.sort(key=lambda x: -x[0])
    lines = []
    for _, m in scored[:3]:
        label = "Correct answer" if m["rating"] == "corrected" else "Approved answer"
        lines.append(f"- User asked: {m['q'][:200]} | {label}: {m['a'][:300]}")
    return "\n".join(lines)


# =====================================================================
# WEB SEARCH
# =====================================================================
TRUSTED = ("wikipedia.org", "bbc.com", "reuters.com", "apnews.com", "britannica.com",
           "nasa.gov", "who.int", "nytimes.com", "cnn.com", "aljazeera.com")
SEARCH_RE = re.compile(
    r"\b(who is|who won|what is|when did|when is|latest|news|today|tonight|yesterday|"
    r"price|how many|current|currently|is it true|score|weather|20\d\d)\b", re.I)


def needs_search(text):
    return bool(SEARCH_RE.search(text))


def is_trusted(url):
    host = urlparse(url).hostname or ""
    if host.endswith(".gov") or host.endswith(".edu") or ".gov." in host or ".edu." in host:
        return True
    return any(host == d or host.endswith("." + d) for d in TRUSTED)


def search_web(query):
    results = []
    # 1. Google Custom Search (optional)
    try:
        gk, gcx = st.secrets.get("GOOGLE_API_KEY", ""), st.secrets.get("GOOGLE_CX", "")
        if gk and gcx:
            g = requests.get("https://www.googleapis.com/customsearch/v1",
                             params={"key": gk, "cx": gcx, "q": query, "num": 5}, timeout=8).json()
            for it in g.get("items", []):
                results.append(f"- {it.get('title','')}: {it.get('snippet','')} (Source: {it.get('link','')})")
            if results:
                return "\n".join(results)
    except Exception as e:
        report("google search", e)
    # 2. Wikipedia
    try:
        w = requests.get("https://en.wikipedia.org/w/api.php", params={
            "action": "query", "generator": "search", "gsrsearch": query, "gsrlimit": 2,
            "prop": "extracts", "exintro": 1, "explaintext": 1, "exsentences": 3, "format": "json"},
            headers={"User-Agent": "EmmanuelAI/1.0"}, timeout=6).json()
        for p in w.get("query", {}).get("pages", {}).values():
            title = p.get("title", "")
            results.append(f"- Wikipedia - {title}: {p.get('extract','')} "
                           f"(Source: https://en.wikipedia.org/wiki/{title.replace(' ', '_')})")
    except Exception as e:
        report("wikipedia", e)
    # 3. DuckDuckGo, trusted domains only
    try:
        try:
            from ddgs import DDGS
        except ImportError:
            from duckduckgo_search import DDGS
        for r in DDGS().text(query, max_results=10):
            link = r.get("href", "")
            if is_trusted(link):
                results.append(f"- {r.get('title','')}: {r.get('body','')} (Source: {link})")
            if len(results) >= 5:
                break
    except Exception as e:
        report("ddgs", e)
    return "\n".join(results[:5])


# =====================================================================
# CHAT (streaming, with model fallback)
# =====================================================================
def build_system(user, lang, web="", mem=""):
    s = SYSTEM_PROMPT + f"\n\nToday's date: {datetime.now():%A, %d %B %Y}.\nThe user's name is {user}."
    if lang != AUTO:
        s += f"\nReply in {lang}."
    if web:
        s += f"\n\nWEB SEARCH RESULTS (use only if relevant):\n{web}"
    if mem:
        s += f"\n\nFROM THIS USER'S APPROVED PAST ANSWERS:\n{mem}"
    return s


def get_history(messages, n=12):
    return [{"role": m["role"], "content": m["content"][:800]} for m in messages[-n:]]


def stream_chat(messages):
    last_err = None
    for model in CHAT_MODELS:
        got_text = False
        try:
            stream = client.chat.completions.create(
                model=model, messages=messages, temperature=0.4, max_tokens=1024, stream=True)
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    got_text = True
                    yield delta
            if got_text:
                return
        except Exception as e:
            last_err = e
            report(f"chat model {model}", e)
            if got_text:  # failed mid-answer - keep what we already showed
                return
    raise last_err or RuntimeError("All chat models failed")


# =====================================================================
# IMAGES  (Gemini first, Groq vision as fallback)
# =====================================================================
def compress_image(img_bytes, max_size=1280):
    try:
        img = ImageOps.exif_transpose(Image.open(io.BytesIO(img_bytes)))  # fixes rotated phone photos
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[3])
            img = bg
        else:
            img = img.convert("RGB")
        img.thumbnail((max_size, max_size))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        return buf.getvalue()
    except Exception as e:
        report("compress_image", e)
        return img_bytes


def gemini_vision(system, history, question, images):
    key = st.secrets.get("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("No GEMINI_API_KEY in secrets")
    contents = [{"role": "user" if m["role"] == "user" else "model", "parts": [{"text": m["content"]}]}
                for m in history]
    while contents and contents[0]["role"] == "model":
        contents.pop(0)
    parts = [{"text": question}] + [
        {"inline_data": {"mime_type": "image/jpeg", "data": base64.b64encode(b).decode()}} for b in images]
    contents.append({"role": "user", "parts": parts})
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
        headers={"x-goog-api-key": key},
        json={"systemInstruction": {"parts": [{"text": system}]}, "contents": contents},
        timeout=45)
    if r.status_code != 200:
        raise RuntimeError(f"Gemini {r.status_code}: {r.text[:200]}")
    return r.json()["candidates"][0]["content"]["parts"][0]["text"]


def groq_vision(system, history, question, images):
    content = [{"type": "text", "text": question}] + [
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}}
        for b in images]
    messages = [{"role": "system", "content": system}] + history + [{"role": "user", "content": content}]
    last_err = None
    for model in GROQ_VISION_MODELS:
        try:
            resp = client.chat.completions.create(model=model, messages=messages, max_tokens=1024, temperature=0.3)
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            report(f"groq vision {model}", e)
    raise last_err or RuntimeError("All vision models failed")


def vision_answer(system, history, question, images):
    try:
        return gemini_vision(system, history, question, images)
    except Exception as e:
        report("gemini_vision", e)
    return groq_vision(system, history, question, images)


# =====================================================================
# VOICE  (speech-to-text with Groq Whisper, text-to-speech with edge-tts)
# =====================================================================
def transcribe_voice(audio_bytes):
    if len(audio_bytes) < 2000:
        return None  # too short to contain speech
    try:
        t = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes), model=WHISPER_MODEL, response_format="text")
        return str(t).strip() or None
    except Exception as e:
        report("transcribe", e)
        return None


def clean_for_tts(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[*_#>`|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()[:700]


async def _tts(text, voice):
    import edge_tts
    out = b""
    async for chunk in edge_tts.Communicate(text, voice).stream():
        if chunk["type"] == "audio":
            out += chunk["data"]
    return out


def speak(text, voice):
    try:
        return asyncio.run(_tts(clean_for_tts(text), voice)) or None
    except Exception as e:
        report("tts", e)
        return None


# =====================================================================
# SESSION + LOGIN
# =====================================================================
for k, v in {"messages": [], "username": None, "uploader_key": 0, "audio_key": 0,
             "last_audio_id": None, "teach_q": None, "pending_audio": None}.items():
    st.session_state.setdefault(k, v)

st.title("🤖 Emmanuel AI")

if not st.session_state.username:
    st.caption("Welcome! Make I remember you.")
    with st.form("login"):
        name = st.text_input("Name / username")
        pin = st.text_input("PIN (4+ characters)", type="password")
        submitted = st.form_submit_button("Continue →")
    if submitted:
        if not name.strip() or len(pin) < 4:
            st.warning("Enter your name and a PIN of at least 4 characters.")
        else:
            ok, msg = login(name.strip(), pin)
            if ok:
                st.session_state.username = name.strip()
                st.session_state.messages = read_json(user_path("chats", name, "json"), [])
                st.rerun()
            else:
                st.error(msg)
    st.stop()

username = st.session_state.username

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown(f"👤 **{username}**  \n{len(st.session_state.messages)} messages saved")
    lang = st.selectbox("🌍 Language", list(LANGUAGES))
    speak_on = st.toggle("🔊 Speak replies", value=False)
    DEBUG = st.toggle("🐞 Debug mode", value=False)
    if st.button("🔄 Switch user"):
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()
    if st.button("🗑️ Clear history"):
        st.session_state.messages = []
        save_chats(username, [])
        st.rerun()


# ---------- FEEDBACK ----------
def rate(idx, kind):
    msgs = st.session_state.messages
    q = msgs[idx - 1]["content"] if idx > 0 else ""
    if kind == "good":
        save_memory(st.session_state.username, q, msgs[idx]["content"], "good")
        st.toast("Noted! I go remember this as correct ✅")
    else:
        st.session_state.teach_q = q
        st.toast("Type the correct answer in your next message and I go learn am 🧠")


# ---------- ATTACHMENTS ----------
with st.expander("📎 Add image  /  🎤 Speak"):
    uploaded = st.file_uploader("Upload image (max 3)", type=["jpg", "jpeg", "png"],
                                accept_multiple_files=True,
                                key=f"uploader_{st.session_state.uploader_key}")
    audio_file = st.audio_input("Speak - any language", key=f"audio_{st.session_state.audio_key}")

uploaded = (uploaded or [])[:3]
if uploaded:
    st.caption(f"📷 {len(uploaded)} image(s) ready - they go with your next message.")

# ---------- CHAT HISTORY ----------
msgs = st.session_state.messages
pending_audio = st.session_state.pending_audio
st.session_state.pending_audio = None  # play once only

for i, m in enumerate(msgs):
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("img"):
            st.caption(f"📷 {m['img']} image(s) attached")
        if m["role"] == "assistant":
            b1, b2, _ = st.columns([1, 1, 6])
            b1.button("👍", key=f"up_{i}", on_click=rate, args=(i, "good"))
            b2.button("👎", key=f"down_{i}", on_click=rate, args=(i, "bad"))
            if i == len(msgs) - 1 and pending_audio:
                st.audio(pending_audio, format="audio/mp3", autoplay=True)

# ---------- INPUT ----------
user_text = None
voice_used = False
if audio_file:
    audio_bytes = audio_file.getvalue()
    audio_id = hashlib.md5(audio_bytes).hexdigest()
    if audio_id != st.session_state.last_audio_id:
        st.session_state.last_audio_id = audio_id
        with st.spinner("Listening..."):
            user_text = transcribe_voice(audio_bytes)
        if user_text:
            voice_used = True
        else:
            st.error("Voice wahala small 🎤 - abeg try again: speak clear, close to the phone, "
                     "and talk for at least 2 seconds.")

typed = st.chat_input("Ask anything - slang, pidgin, any language...")
if typed:
    user_text = typed

# ---------- ANSWER ----------
if user_text:
    images = [compress_image(f.getvalue()) for f in uploaded]
    history = get_history(msgs)  # taken BEFORE adding the new message

    if st.session_state.teach_q:  # user pressed 👎 and is now giving the right answer
        save_memory(username, st.session_state.teach_q, user_text, "corrected")
        st.session_state.teach_q = None
        st.toast("Learned! 🧠")

    msgs.append({"role": "user", "content": user_text, **({"img": len(images)} if images else {})})
    save_chats(username, msgs)

    with st.chat_message("user"):
        st.markdown(user_text)
        for im in images:
            st.image(im, width=250)

    answer = None
    with st.chat_message("assistant"):
        try:
            web = ""
            if not images and needs_search(user_text):
                with st.spinner("Searching the web..."):
                    web = search_web(user_text)
            system = build_system(username, lang, web, relevant_memories(username, user_text))
            if images:
                with st.spinner("Looking at your image..."):
                    answer = vision_answer(system, history, user_text, images)
                st.markdown(answer)
            else:
                chat_messages = ([{"role": "system", "content": system}] + history
                                 + [{"role": "user", "content": user_text}])
                answer = st.write_stream(stream_chat(chat_messages))
        except Exception as e:
            report("answer", e)
            st.error(FRIENDLY_ERROR)

    if answer:
        msgs.append({"role": "assistant", "content": answer})
        save_chats(username, msgs)
        if speak_on:
            st.session_state.pending_audio = speak(answer, LANGUAGES[lang])
        st.session_state.uploader_key += 1  # clears the uploaded images
        if voice_used:
            st.session_state.audio_key += 1  # clears the recorder
        st.rerun()  # redraw history so 👍/👎 buttons appear
