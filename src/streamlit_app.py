import streamlit as st
import json
import os
from graph.supervisor_agent import run_supervisor


# persist memory
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


# streamlit config
st.set_page_config(
    page_title="Multi-Source AI Assistant",
    layout="wide"
)

st.title(" Multi-Source AI Assistant")
st.caption("LangGraph Supervisor · SQL + RAG Routing")

st.divider()

# initialize history
if "history" not in st.session_state:
    st.session_state.history = load_history()


# user input
question = st.text_input("Ask your question:")

if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        with st.spinner("Thinking..."):
            result = run_supervisor(question, st.session_state.history)

            # Supervisor returns updated history
            st.session_state.history = result.get("history", st.session_state.history)
            save_history(st.session_state.history)

            agent_used = result.get("agent_used", "UNKNOWN")
            response = result.get("response", {})

            st.success(f"Agent Used: {agent_used}")

        # sql_agent output
        
            if agent_used == "SQL_AGENT":
                st.markdown("### Answer")
                st.write(response.get("answer", ""))

                sql_result = response.get("result", {})
                if sql_result.get("generated_sql"):
                    st.markdown("### Generated SQL")
                    st.code(sql_result["generated_sql"], language="sql")

                if sql_result.get("data"):
                    st.markdown("### Query Results")
                    st.dataframe(sql_result["data"])
                else:
                    st.warning("No data returned.")

           
           # rag_agent output
            elif agent_used == "RAG_AGENT":
                st.markdown("### Answer")
                st.write(response.get("answer", ""))

                sources = response.get("sources", [])
                if sources:
                    st.markdown("### Sources")
                    for src in sources:
                        st.write(
                            f"- PDF: {src.get('pdf')} | "
                            f"Page: {src.get('page')} | "
                            f"Chunk: {src.get('chunk_id')}"
                        )

          # guardrail
            else:
                st.markdown("### Response")
                st.write(response.get("answer", ""))


# conversation history
st.divider()
st.subheader(" Conversation History")

if st.session_state.history:
    for turn in reversed(st.session_state.history):
        st.markdown(f"**Q:** {turn.get('question')}")
        st.markdown(f"**Agent:** {turn.get('agent')}")
        st.markdown(f"**A:** {turn.get('response', {}).get('answer', '')}")

        if turn.get("agent") == "SQL_AGENT":
            result = turn.get("response", {}).get("result", {})
            if result.get("generated_sql"):
                st.code(result["generated_sql"], language="sql")
            if result.get("data"):
                st.dataframe(result["data"])

        if turn.get("agent") == "RAG_AGENT":
            sources = turn.get("response", {}).get("sources", [])
            if sources:
                st.markdown("**Sources:**")
                for src in sources:
                    st.write(
                        f"- PDF: {src.get('pdf')} | "
                        f"Page: {src.get('page')} | "
                        f"Chunk: {src.get('chunk_id')}"
                    )

        st.markdown("---")
else:
    st.info("No conversation yet. Ask a question to begin.")
