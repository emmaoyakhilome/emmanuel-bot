# Add at top with other imports
import datetime

# Add after st.session_state.messages is defined
if "all_chats" not in st.session_state:
    st.session_state.all_chats = []

# Inside the chat input block, after you get answer 'ans'
# Add this:
st.session_state.all_chats.append({
    "time": str(datetime.datetime.now()),
    "question": prompt,
    "answer": ans
})

# In your sidebar, add this admin section at bottom:
with st.sidebar:
    # ... your existing sidebar code ...
    st.write("---")
    st.write("🔒 Admin")
    admin_pass = st.text_input("Admin password", type="password")
    if admin_pass == "emmanuel123": # change this password!
        st.write(f"Total chats: {len(st.session_state.all_chats)}")
        for chat in st.session_state.all_chats[::-1]:
            st.write(f"**Q:** {chat['question']}")
            st.write(f"**Time:** {chat['time']}")
            st.write("---")
