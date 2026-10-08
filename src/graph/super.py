# # src/graph/supervisor_agent.py

# import os
# from dotenv import load_dotenv
# from langchain_groq import ChatGroq
# from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
# from langchain_core.tools import Tool

# from .sql_agent import run_sql_agent
# from .rag_agent import run_rag_agent


# load_dotenv()

# # llm
# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",  # change to smaller model if needed
#     temperature=0,
#     groq_api_key=os.environ["GROQ_API_KEY"],
# )


# # wrap agent as tool
# sql_tool = Tool(
#     name="SQL",
#     description="Handles SQL-related questions using the Northwind database",
#     func=lambda question: run_sql_agent(question)["answer"]
# )

# rag_tool = Tool(
#     name="RAG",
#     description="Handles research/medical/scientific questions",
#     func=lambda question: run_rag_agent(question)["answer"]
# )


# # prompt
# SUPERVISOR_PROMPT = """
# You are a routing agent.

# Decide where the question should go.

# Rules:
# - SQL → customers, orders, sales, business data, Northwind database
# - RAG → research papers, clinical trials, medical, scientific knowledge

# Output ONLY one word: SQL or RAG
# """

# # create agent
# supervisor_agent = create_agent(
#     model=llm,
#     tools=[sql_tool, rag_tool],   # pass agents as tools
#     system_prompt=SUPERVISOR_PROMPT,
#     name="supervisor_agent",
# )


# # runner function
# def run_supervisor(question: str) -> dict:
#     """Run supervisor agent and route question to SQL or RAG agent."""
#     try:
#         # Step 1: Ask supervisor to decide route
#         result = supervisor_agent.invoke({"messages": [HumanMessage(content=question)]})
#         decision = result["messages"][-1].content.strip().upper()

#         # Step 2: Validate supervisor decision
#         if decision not in ["SQL", "RAG"]:
#             return {
#                 "route": "block",
#                 "response": "Please ask a question related to SQL or research documents."
#             }

#         # Step 3: Call the selected agent
#         answer = sql_tool.func(question) if decision == "SQL" else rag_tool.func(question)

#         return {
#             "route": decision,
#             "response": answer
#         }

#     except Exception as e:
#         return {
#             "route": "error",
#             "response": f"Supervisor agent failed: {e}"
#         }


# if __name__ == "__main__":
#     print("Supervisor Agent CLI (type 'exit' to quit)\n" + "-"*50)
#     while True:
#         question = input("Enter your question: ").strip()
#         if question.lower() in ["exit", "quit"]:
#             break

#         print("\nRunning supervisor agent...")
#         result = run_supervisor(question)
#         print("\nRouting result:")
#         print(result)
#         print("-" * 50)

# src/graph/supervisor_agent.py

from langgraph_supervisor import create_supervisor
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ---------------------------
# Import your existing agents
# ---------------------------
from .sql_agent import sql_agent  # prebuilt SQL agent
from .rag_agent import rag_agent  # prebuilt RAG agent

# ---------------------------
# LLM for Supervisor
# ---------------------------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# ---------------------------
# Supervisor prompt
# ---------------------------
SUPERVISOR_PROMPT = """
You are a Supervisor agent.

Instructions:
- Determine if the user's question should go to:
    1. SQL Agent (Northwind database queries)
    2. RAG Agent (PubMed / research queries)
- Route the question to the correct agent.
- NEVER answer directly; only call the correct agent.
- Respond only with 'SQL' or 'RAG'.
"""

# ---------------------------
# Create Supervisor
# ---------------------------
supervisor = create_supervisor(
    agents=[sql_agent, rag_agent],       # Pass the prebuilt agents directly
    model=llm,
    prompt=SUPERVISOR_PROMPT,
    response_format="text",
    parallel_tool_calls=False,
    supervisor_name="react_supervisor"
)

# ---------------------------
# Compile Supervisor
# ---------------------------
app = supervisor.compile()

# ---------------------------
# Runner function
# ---------------------------
def run_supervisor(query: str):
    """
    Call the Supervisor agent and return the result.
    """
    state_graph = app.invoke({"input":HumanMessage(query)})
    return state_graph

# ---------------------------
# Test
# ---------------------------
if __name__ == "__main__":
    q = input("Enter your question for Supervisor Agent: ")
    result = run_supervisor(q)
    print("\nSupervisor output:")
    print(result)

