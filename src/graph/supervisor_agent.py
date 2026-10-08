import json
import re
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from typing import TypedDict, Literal, Dict, Any
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

from .guardrail import guardrail_node
from .sql_agent import run_sql_agent
from .rag_agent import run_rag_agent

load_dotenv()


# llm
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
)

SUPERVISOR_PROMPT = """
Classify the user question into ONE category.

Return ONLY JSON:
{"route": "sql" | "rag"}

sql → tables, counts, customers, orders
rag → medical, scientific, document-based
"""

def classify_query(question: str) -> str:
    response = llm.invoke([HumanMessage(content=f"{SUPERVISOR_PROMPT}\n{question}")])
    try:
        return json.loads(response.content)["route"]
    except Exception:
        # Default to RAG if classification fails
        return "rag"



def is_valid_question(question: str) -> bool:
    q = question.strip().lower()

    if len(q) < 6:
        return False

    if not re.search(r"[aeiou]", q):
        return False

    keywords = [
        "list", "show", "count", "customer", "order", "product",
        "study", "trial", "outcome", "disease", "patient",
        "clinical", "treatment", "effect"
    ]
    return any(k in q for k in keywords)



# state
class State(TypedDict):
    question: str
    route: Literal["sql", "rag"]
    response: Dict[str, Any]
    agent_used: str
    allowed: bool
    history: list



# supervisor agent
def supervisor_node(state: State) -> State:
    """
    This replaces the old router_node.
    Classifies the question into "sql" or "rag".
    """
    state["route"] = classify_query(state["question"])
    return state

def sql_node(state: State) -> State:
    result = run_sql_agent(state["question"])

    state["response"] = {
        "answer": "Here is the result for your SQL query.",
        "result": {
            "tables_used": result.get("tables_used", []),
            "generated_sql": result.get("generated_sql", ""),
            "data": result.get("data", [])
        }
    }
    state["agent_used"] = "SQL_AGENT"

    state.setdefault("history", []).append({
        "question": state["question"],
        "agent": "SQL_AGENT",
        "response": state["response"]
    })
    return state

def rag_node(state: State) -> State:
    question = state["question"]

    # Ambiguity handling
    ambiguous_terms = [
        "top", "best", "leading", "major", "famous",
        "good", "important", "popular"
    ]

    if any(term in question.lower() for term in ambiguous_terms):
        state["response"] = {
            "answer": (
                "Your question is ambiguous(sql+rag).\n"
                "Please clarify what information you are referring to so I can proceed."
            ),
            "sources": []
        }

        state["agent_used"] = "RAG_AGENT"
        return state

    # Real RAG execution
    result = run_rag_agent(question)

    state["response"] = result
    state["agent_used"] = "RAG_AGENT"

    state.setdefault("history", []).append({
        "question": question,
        "agent": "RAG_AGENT",
        "response": result
    })

    return state


# supervisor graph
def build_supervisor_graph():
    graph = StateGraph(State)

    graph.add_node("guardrail", guardrail_node)
    graph.add_node("supervisor", supervisor_node)  # renamed from "router"
    graph.add_node("sql_agent", sql_node)
    graph.add_node("rag_agent", rag_node)

    graph.set_entry_point("guardrail")

    # Guardrail decides if blocked or go to supervisor
    graph.add_conditional_edges(
        "guardrail",
        lambda s: "blocked" if not s["allowed"] else "supervisor",
        {"blocked": END, "supervisor": "supervisor"}
    )

    # Supervisor routes to SQL or RAG
    graph.add_conditional_edges(
        "supervisor",
        lambda s: s["route"],  # only "sql" or "rag"
        {
            "sql": "sql_agent",
            "rag": "rag_agent",
        }
    )

    graph.add_edge("sql_agent", END)
    graph.add_edge("rag_agent", END)

    return graph.compile()

supervisor_app = build_supervisor_graph()


# run supervisor
def run_supervisor(question: str, history=None) -> dict:
    final_state = supervisor_app.invoke({
        "question": question,
        "route": "",
        "response": {},
        "agent_used": "",
        "allowed": True,
        "history": history or []
    })

    # Add CAP005 as the overall agent name
    return {
        "agent_name": "CAP005",  # <-- NEW
        "agent_used": final_state.get("agent_used"),  # still SQL_AGENT / RAG_AGENT / GUARDRAIL
        "response": final_state.get("response"),
        "history": final_state.get("history", [])
    }
