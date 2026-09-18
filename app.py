import streamlit as st
from groq import Groq
import base64
from gtts import gTTS
import io
from datetime import datetime as dt

st.set_page_config(page_title="Emmanuel AI", page_icon="🤖", layout="centered")

GROQ_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_KEY)

SYSTEM_PROMPT = """
You are Emmanuel AI, built by Emmanuel Ebhota.
You were created by Emmanuel Ebhota in Nigeria.
You are NOT OpenAI, NOT ChatGPT, NOT Meta AI, NOT Google.
If anyone asks who built you, your creator is Emmanuel Ebhota.
Always answer as Emmanuel AI. Be helpful and simple for Nigerian students.
"""

st.title("🤖 Emmanuel AI")
st.caption("Built by Emmanuel Ebhota | Ask me anything")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

def log_to_sheet(user_msg, ai_msg):
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        creds_dict = st.secrets["gspread"]
        scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gc = gspread.authorize(creds)
        sheet = gc.open("Emmanuel AI Logs").sheet1
        now = dt.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, user_msg, ai_msg])
    except:
        pass

uploaded_file = st.file_uploader("📷 Upload image (optional)", type=["jpg","jpeg","png"])
audio_file = st.audio_input("🎤 Tap to speak")
user_text = None

if audio_file:
    try:
        transcription = client.audio.transcriptions.create(
            file=(audio_file.name, audio_file.read()),
            model="whisper-large-v3",
            response_format="text"
        )
        user_text = transcription
        st.success(f"You said: {user_text}")
    except Exception as e:
        st.error(f"Voice error: {e}")

if not user_text:
    if chat_input := st.chat_input("Message Emmanuel AI..."):
        user_text = chat_input

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)
        if uploaded_file:
            st.image(uploaded_file, width=250)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                if uploaded_file:
                    b64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
                    response = client.chat.completions.create(
                        model="meta-llama/llama-4-scout-17b-16e-instruct",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": [
                                {"type": "text", "text": user_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
                            ]}
                        ]
                    )
                else:
                    response = client.chat.completions.create(
                        model="openai/gpt-oss-20b",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_text}
                        ]
                    )

                ans = response.choices[0].message.content
                st.markdown(ans)

                try:
                    tts = gTTS(ans[:3500], lang='en')
                    out = io.BytesIO()
                    tts.write_to_fp(out)
                    out.seek(0)
                    st.audio(out, format="audio/mp3")
                except:
                    pass

                st.session_state.messages.append({"role": "assistant", "content": ans})
                log_to_sheet(user_text, ans)

            except Exception as e:
                st.error(f"Error: {e}")
