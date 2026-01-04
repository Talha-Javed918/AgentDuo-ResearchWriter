import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/research"

st.set_page_config(
    page_title="Multi-Agent Research System",
    layout="wide"
)

st.title("🧠 Multi-Agent Research & Report System")

# -----------------------------------
# SESSION STATE
# -----------------------------------

if "history" not in st.session_state:
    st.session_state.history = []

if "current_turn" not in st.session_state:
    st.session_state.current_turn = "idle"   # idle | user | agent

# -----------------------------------
# DISPLAY HISTORY (Chat-style)
# -----------------------------------
chat_container = st.container()

with chat_container:
    for item in st.session_state.history:
        st.markdown(f"**🧑‍💻 You:** {item['topic']}")
        st.markdown(f"**🤖 Agent:** {item['report']}")
        st.divider()

# -----------------------------------
# INPUT AT BOTTOM
# -----------------------------------
st.markdown("<br>", unsafe_allow_html=True)  # Spacer

input_col1, input_col2 = st.columns([8, 1])

with input_col1:
    topic = st.text_input("Type your research topic here...", key="input_topic")

with input_col2:
    if st.button("Send"):
        if not topic.strip():
            st.error("Please enter a topic.")
        else:
            st.session_state.current_turn = "agent"

            # Add user's message to chat immediately
            st.session_state.history.append({
                "topic": topic,
                "report": "..."  # Placeholder while agent works
            })

            # Refresh the chat container
            chat_container.empty()
            with chat_container:
                for item in st.session_state.history:
                    st.markdown(f"**🧑‍💻 You:** {item['topic']}")
                    st.markdown(f"**🤖 Agent:** {item['report']}")
                    st.divider()

            with st.spinner("🤖 Agents are researching and writing..."):
                response = requests.post(
                    API_URL,
                    json={"topic": topic}
                )

                if response.status_code == 200:
                    report = response.json()["report"]
                    # Update the last entry with actual agent response
                    st.session_state.history[-1]["report"] = report
                    st.session_state.current_turn = "idle"
                else:
                    st.error("API error occurred.")
                    st.session_state.history[-1]["report"] = "Error occurred!"
                    st.session_state.current_turn = "idle"

            # Refresh chat after agent response
            chat_container.empty()
            with chat_container:
                for item in st.session_state.history:
                    st.markdown(f"**🧑‍💻 You:** {item['topic']}")
                    st.markdown(f"**🤖 Agent:** {item['report']}")
                    st.divider()

# -----------------------------------
# TURN INDICATOR
# -----------------------------------
if st.session_state.current_turn == "agent":
    st.info("🤖 Agent is working...")
else:
    st.success("✅ Ready for next topic")
