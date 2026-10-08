import os
import json
import asyncio
import re
from dotenv import load_dotenv
import nest_asyncio
import string

from fastmcp.client import Client
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq


load_dotenv()
nest_asyncio.apply()

MCP_URL = "http://127.0.0.1:9000/mcp"


RAG_REACT_PROMPT = """
You are a STRICT Retrieval-Augmented Generation (RAG) agent.

Rules (MANDATORY):
- You MUST call the retrieval tool for scientific or medical questions.
- Do NOT answer from your own knowledge.
- Do NOT summarize or explain.
- Return ONLY retrieved text verbatim.
- If nothing is found, respond exactly:
  "Not found in retrieved PubMed documents."
"""


def is_invalid_question(q: str) -> bool:
    q = q.strip().lower()
    if len(q) < 6:
        return True
    if not re.search(r"[aeiou]", q):
        return True
    if re.fullmatch(r"[a-z]{6,}", q) and len(set(q)) < 4:
        return True
    return False


def is_negative_question(q: str) -> bool:
    """
    Detect questions that imply 'no answer', e.g., containing doesn't, not, none.
    """
    triggers = ["doesn't", "does not", "not found", "none", "no", "doesnt"]
    q = q.lower()
    return any(t in q for t in triggers)


# clean text
def clean_text(s: str) -> str:
    printable = set(string.printable)
    return ''.join(filter(lambda x: x in printable, s))

def clean_rag_answer(text: str) -> str:
    """
    Cleans the RAG agent output by removing garbled chunks
    and keeping only meaningful lines.
    """
    lines = text.split("\n")
    clean_lines = [l.strip() for l in lines if len(l.strip()) > 20]
    return "\n".join(clean_lines[:5])  # keep first 5 meaningful lines


# mcp tool loader
async def load_rag_tools(collected_sources: list):
    tools = []

    async with Client(MCP_URL) as client:
        mcp_tools = await client.list_tools()

        for tool_def in mcp_tools:
            schema = tool_def.inputSchema or {}
            required = schema.get("required", [])
            if len(required) != 1:
                continue

            input_key = required[0]
            tool_name = tool_def.name
            tool_desc = tool_def.description or "PubMed RAG tool"

            def make_sync_tool(name, key):
                def sync_tool(question: str):
                    async def _call():
                        async with Client(MCP_URL) as inner:
                            return await inner.call_tool(name, {key: question})

                    try:
                        response = asyncio.get_event_loop().run_until_complete(_call())
                    except RuntimeError:
                        response = asyncio.run(_call())

                    if not response.content:
                        return "Not found in retrieved PubMed documents."

                    texts = []

                    for item in response.content:
                        raw_text = getattr(item, "text", None)
                        if not raw_text:
                            continue
                        try:
                            docs = json.loads(raw_text)
                        except Exception:
                            continue
                        if not isinstance(docs, list):
                            continue
                        for d in docs:
                            content = str(d.get("content", "")).strip()
                            meta = d.get("metadata", {})
                            if not content:
                                continue
                            collected_sources.append({
                                "pdf": meta.get("pdf"),
                                "page": meta.get("page"),
                                "chunk_id": meta.get("chunk_id"),
                            })
                            texts.append(clean_text(content))

                    return (
                        "\n\n".join(texts)
                        if texts
                        else "Not found in retrieved PubMed documents."
                    )

                return sync_tool

            tools.append(
                Tool(
                    name=tool_name,
                    description=tool_desc,
                    func=make_sync_tool(tool_name, input_key),
                    return_direct=True,
                )
            )

    if not tools:
        raise RuntimeError("No RAG tools found on MCP server.")

    return tools


# llm
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.environ["GROQ_API_KEY"],
)


def run_rag_agent(question: str) -> dict:
    try:
        # Check for gibberish or too short question
        if is_invalid_question(question) or is_negative_question(question):
            return {
                "answer": "Not found in retrieved PubMed documents.",
                "sources": []
            }

        collected_sources = []
        tools = asyncio.run(load_rag_tools(collected_sources))

        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=RAG_REACT_PROMPT,
            name="rag_agent",
        )

        result = agent.invoke({
            "messages": [HumanMessage(content=question)]
        })

        messages = result.get("messages", [])

        final_answer = (
            messages[-1].content
            if messages
            else ""
        )

        # Debug
        print("\n===== RAG DEBUG =====")
        print("Question:", question)
        print("Sources Found:", len(collected_sources))
        print("Sources:", collected_sources)
        print("Final Answer:", final_answer)
        print("=====================\n")

        # Return answer directly (don't clean it)
        if final_answer and str(final_answer).strip():
            return {
                "answer": str(final_answer),
                "sources": collected_sources
            }

        return {
            "answer": "Not found in retrieved PubMed documents.",
            "sources": collected_sources
        }

    except Exception as e:
        print("RAG ERROR:", str(e))

        return {
            "answer": f"Error: {str(e)}",
            "sources": []
        }

if __name__ == "__main__":
    q = input("Enter your RAG question: ")
    res = run_rag_agent(q)
    print("\nAnswer:\n")
    print(res["answer"])
    print("\nSources:\n")
    for s in res["sources"]:
        print(s)
