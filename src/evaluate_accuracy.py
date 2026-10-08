import asyncio
from graph.workflow import build_workflow

workflow = build_workflow()

test_cases = [
    {"q": "compare sales of chai and chang", "expected": "sql"},
    {"q": "list customers from Germany", "expected": "sql"},
    {"q": "Who were the participants in the trial?", "expected": "rag"},
    {"q": "Explain the intervention phases", "expected": "rag"},
    {"q": "sales and trial info", "expected": "ambiguous"}
]

async def evaluate():
    correct = 0
    failures = []

    for case in test_cases:
        result = await workflow.ainvoke({"question": case["q"]})
        predicted = result.get("route")

        if predicted == case["expected"]:
            correct += 1
        else:
            failures.append({
                "question": case["q"],
                "expected": case["expected"],
                "predicted": predicted
            })

    accuracy = correct / len(test_cases)

    print("\nRouting Accuracy:", accuracy)
    print("\nFailure Cases:")
    for f in failures:
        print(f)

asyncio.run(evaluate())
