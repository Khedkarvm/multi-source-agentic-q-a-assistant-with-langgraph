# test_routing.py
from graph.supervisor_agent import run_supervisor

# Define test queries
test_queries = [
    "Which product had highest sales in 2022?",  # SQL
    "List customers from Germany",  # SQL
    "What were the outcomes of trial X?",  # RAG
    "Tell me about OCD TMS measures",  # RAG
    "Hi, how are you?",  # Guardrail
    "Top 3 products by units in stock",  # SQL
]

# Run each query through supervisor
for q in test_queries:
    res = run_supervisor(q)
    print("-" * 80)
    print(f"Query: {q}")
    print(f"Agent Used: {res['agent_used']}")
    print(f"Answer: {res['response']['answer']}")
    print("-" * 80)
