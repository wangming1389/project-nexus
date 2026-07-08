import streamlit as st
from datetime import datetime
from chat import ask

st.set_page_config(
    page_title="Bot Support",
    page_icon="🤖",
    layout="centered",
)

st.title("Bot RAG Support")
st.markdown(
    "Ask questions about the indexed knowledge base."
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "time" in message:
            st.caption(message["time"])

if prompt := st.chat_input("How do I add a YouTube video?"):
    current_time = datetime.now().strftime("%H:%M")

    with st.chat_message("user"):
        st.markdown(prompt)
        st.caption(current_time)
    st.session_state.messages.append({"role": "user", "content": prompt, "time": current_time})

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                response = ask(prompt)
            except Exception as e:
                response = f"An error occurred: {e}"
        response = response.replace("Article URL:", "\nArticle URL:")
        st.markdown(response)
        
        reply_time = datetime.now().strftime("%H:%M")
        st.caption(reply_time)
    st.session_state.messages.append({"role": "assistant", "content": response, "time": reply_time})
