# orchestrator.py

from graph.guardrail import guardrail_node
from graph.supervisor_agent import run_supervisor
from graph.sql_agent import run_sql_agent
from graph.rag_agent import run_rag_agent

# Simple in-memory conversation history
conversation_state = {"history": []}


def run_query(question: str) -> dict:
    """
    Orchestrates the multi-agent system:
    - Guardrail → block off-topic/greetings
    - Supervisor → route SQL vs RAG
    - SQL or RAG agent execution
    - Graceful fallback and user-friendly responses
    Returns the latest query result.
    """
    # save question in history
    conversation_state["history"].append({"query": question})

    
    # guardil_check
    guard_result = guardrail_node(question)
    if guard_result["route"] == "block":
        conversation_state["history"][-1].update({
            "agent": guard_result["agent_used"],
            "status": "blocked",
            "answer": guard_result.get("response"),
        })
        return conversation_state["history"][-1]

    
    # supervisor routing 
    route_result = run_supervisor(question)
    route = route_result.get("route", "block")

   
   # sql_agent route
    if route == "sql":
        sql_result = run_sql_agent(question)
        conversation_state["history"][-1].update({
            "agent": "sql_agent",
            "status": sql_result.get("status", "success"),
            "answer": sql_result.get("answer", ""),
            "sources": sql_result.get("sources", {})
        })
        return conversation_state["history"][-1]

   
    # rag_agent route
    if route == "rag":
        rag_result = run_rag_agent(question)
        conversation_state["history"][-1].update({
            "agent": "rag_agent",
            "status": rag_result.get("status", "success"),
            "answer": rag_result.get("answer", ""),
            "sources": rag_result.get("sources", [])
        })
        return conversation_state["history"][-1]

    
    # safety fallback
    conversation_state["history"][-1].update({
        "agent": "system",
        "status": "failed",
        "answer": "Could not process your question. Please try again with a valid query.",
        "reason": "Unknown routing error"
    })
    return conversation_state["history"][-1]




if __name__ == "__main__":
    while True:
        question = input("\nEnter your question (or 'exit' to quit): ").strip()
        if question.lower() in ("exit", "quit"):
            break
        result = run_query(question)
        print("\nAnswer:", result["answer"])
        print("Agent Used:", result["agent"])
        print("Status:", result["status"])
