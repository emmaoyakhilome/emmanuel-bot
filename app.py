voice_text = None
if audio_file and audio_file.id != st.session_state.last_audio_id:
    with st.spinner("Transcribing..."):
        try:
            # FIXED VOICE CODE
            audio_bytes = audio_file.getvalue()
            tr = client.audio.transcriptions.create(
                model="whisper-large-v3-turbo", # turbo is faster and stable
                file=("voice.wav", audio_bytes, "audio/wav")
            )
            voice_text = tr.text
            st.session_state.last_audio_id = audio_file.id
            st.success(f"You said: {voice_text}")
        except Exception as e:
            st.error(f"Voice error: {e}")
            print(e) # check logs
