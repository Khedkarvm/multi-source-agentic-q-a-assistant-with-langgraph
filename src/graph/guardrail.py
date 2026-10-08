import random
import string
from typing import TypedDict

POLITE_RESPONSES = [
    "Hi! Please ask a question related to Northwind data or PubMed documents."
]

OFF_TOPIC_KEYWORDS = {"hi", "hii", "hello", "hey", "how are you", "how r u", "what is joke", "weather", "quantum unicorn", "what is your name"}

# Define State type if needed
class State(TypedDict):
    question: str
    route: str
    response: dict
    agent_used: str
    allowed: bool
    history: list

def guardrail_node(state: State) -> State:
    q = state["question"].lower().strip()
    q_clean = q.translate(str.maketrans("", "", string.punctuation))
    words = q_clean.split()

    for keyword in OFF_TOPIC_KEYWORDS:
        if keyword in words or q_clean == keyword:
            state["allowed"] = False
            state["agent_used"] = "GUARDRAIL"
            state["response"] = {"answer": random.choice(POLITE_RESPONSES)}
            # Append to history if available
            if "history" not in state:
                state["history"] = []
            state["history"].append({
                "question": state["question"],
                "agent": state["agent_used"],
                "response": state["response"]
            })
            return state

    state["allowed"] = True
    return state
