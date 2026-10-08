from fastmcp import FastMCP
from super_mcp.sql_tool_helpers import run_sql_query
from super_mcp.rag_tool_helper import doc_search_tool

mcp = FastMCP(name="unified-mcp-server")

# ---------------------------
# SQL tool
# ---------------------------
@mcp.tool()
def sql_tool(sql_query: str) -> str:
    """Execute SQL query on Northwind database"""
    return str(run_sql_query(sql_query))

# ---------------------------
# RAG tool
# ---------------------------
@mcp.tool()
def rag_tool(question: str) -> list[dict]:
    """
    Retrieve PubMed chunks with metadata.
    Returns a list of dicts:
    [
        {"content": "...", "metadata": {...}},
        ...
    ]
    """
    return doc_search_tool(question)  # Already returns list[dict]


# ---------------------------
# Run MCP server
# ---------------------------
if __name__ == "__main__":
    mcp.run(
        transport="http",
        host="127.0.0.1",
        port=9000
    )
