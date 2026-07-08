import streamlit as st
from chat import ask

st.set_page_config(
    page_title="OptiBot Support",
    page_icon="🤖",
    layout="centered",
)

st.title("🤖 OptiBot RAG Support")
st.markdown(
    "Ask me anything about OptiSigns based on the knowledge base!"
)

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("How do I add a YouTube video?"):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            try:
                response = ask(prompt)
            except Exception as e:
                response = f"An error occurred: {e}"
        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})
