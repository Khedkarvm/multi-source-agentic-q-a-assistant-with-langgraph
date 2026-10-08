from pathlib import Path
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------------------
# Paths & Embeddings
# ---------------------------
CHROMA_PATH = Path(r"D:\Neuleap Training\Capstone_Project_Rag\chroma_db")

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ---------------------------
# Vector DB
# ---------------------------
vectordb = Chroma(
    collection_name="langchain",
    persist_directory=str(CHROMA_PATH),
    embedding_function=embeddings
)

print("Chroma Path:", CHROMA_PATH)

try:
    print("Collection Count:", vectordb._collection.count())
except Exception as e:
    print("Count Error:", e)

# ---------------------------
# RAG Search Tool Helper
# ---------------------------
def doc_search_tool(query: str) -> list[dict]:
    """
    Retrieve top 5 documents from Chroma DB with page content and metadata.
    """

    if not query or len(query.strip()) < 3:
        return []

    try:
        docs = vectordb.similarity_search(query, k=5)

        print(f"\nQuery: {query}")
        print(f"Retrieved Docs: {len(docs)}")

        results = []

        for doc in docs:
            results.append({
                "content": doc.page_content,
                "metadata": doc.metadata
            })

        return results

    except Exception as e:
        print("Retrieval Error:", str(e))

        return [{
            "content": "",
            "metadata": {
                "error": str(e)
            }
        }]

# ---------------------------
# Test block
# ---------------------------
if __name__ == "__main__":

    test_query = "What is OCD?"

    results = doc_search_tool(test_query)

    print("\n===== RESULTS =====\n")

    for idx, r in enumerate(results, start=1):
        print(f"Result {idx}")
        print("Content:")
        print(r["content"])
        print("\nMetadata:")
        print(r["metadata"])
        print("-" * 80)