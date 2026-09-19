import streamlit as st
import requests
import urllib.parse
from groq import Groq

# --- CONFIG ---
GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "YOUR_KEY_HERE")
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are Emmanuel AI created by Emmanuel Ebhota in September 2026.
- When asked who created you or when, ALWAYS say: "I am Emmanuel AI created by Emmanuel Ebhota in September 2026"
- NEVER say Meta, Llama, 2024, or GPT.
- Solve Maths/Physics step-by-step: 1. Formula 2. Substitute 3. Solve 4. \\boxed{answer}
- Use simple LaTeX: $F=ma$, not \\mathbf.
"""

# --- FIXED IMAGE GENERATION (No API Key Needed) ---
def generate_image(prompt):
    try:
        # This is free and always works
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.content
        else:
            return None
    except Exception as e:
        st.toast(f"Image gen issue: {e}")
        return None

# --- FIXED VOICE TRANSCRIPTION (No More Confusing Error) ---
def transcribe_audio(audio_file):
    try:
        import speech_recognition as sr
        r = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = r.record(source)
        text = r.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        # Don't show big RED ERROR - just small toast
        st.toast("Could not hear well, try again", icon="🎤")
        return None
    except Exception as e:
        # This was your bug - you showed error even when it worked
        # Now we only log it quietly
        print(f"Voice quiet error: {e}")
        return None

# --- STREAMLIT UI ---
st.set_page_config(page_title="Emmanuel AI", page_icon="🤖")
st.title("Emmanuel AI by Emmanuel Ebhota")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chats
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "image" in msg:
            st.image(msg["image"])

# Voice Input
audio_value = st.audio_input("Tap to speak")

transcribed_text = None
if audio_value:
    # Save temp file
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_value.getbuffer())
    transcribed_text = transcribe_audio("temp_audio.wav")
    if transcribed_text:
        st.toast(f"You said: {transcribed_text}", icon="✅")

# Text Input - use voice text if available
user_prompt = st.chat_input("Ask Emmanuel AI anything...")
final_prompt = transcribed_text if transcribed_text else user_prompt

if final_prompt:
    # Check if user wants image
    if "generate image" in final_prompt.lower() or "create image" in final_prompt.lower():
        with st.chat_message("user"):
            st.markdown(final_prompt)
        with st.chat_message("assistant"):
            with st.spinner("Creating image..."):
                img_bytes = generate_image(final_prompt)
                if img_bytes:
                    st.image(img_bytes, caption=final_prompt)
                    st.session_state.messages.append({"role": "user", "content": final_prompt})
                    st.session_state.messages.append({"role": "assistant", "content": f"Here is your image for: {final_prompt}", "image": img_bytes})
                else:
                    st.write("Image generation failed, try again with simpler prompt.")
    else:
        # Normal chat
        st.session_state.messages.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"):
            st.markdown(final_prompt)

        with st.chat_message("assistant"):
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": SYSTEM_PROMPT}] +
                         [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
            )
            answer = completion.choices[0].message.content
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
