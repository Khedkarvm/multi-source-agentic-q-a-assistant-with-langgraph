import os
from graph.supervisor_agent import build_supervisor_graph
from langgraph.graph import END


# output directoy
OUTPUT_DIR = "graphs_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# graph
try:
    supervisor_graph = build_supervisor_graph()
    
    # Draw the graph as Mermaid PNG
    supervisor_png = supervisor_graph.get_graph().draw_mermaid_png()
    
    # Save to file
    supervisor_path = os.path.join(OUTPUT_DIR, "supervisor_full_graph.png")
    with open(supervisor_path, "wb") as f:
        f.write(supervisor_png)
    
    print(f" Supervisor graph saved at: {supervisor_path}")
except Exception as e:
    print(f" Failed to generate supervisor graph: {e}")

print(" Graph generation completed!")
