import asyncio
from fastmcp.client import Client  # Async client

async def main():
    async with Client("http://127.0.0.1:9001/mcp") as client:
        # Call the RAG tool with a real query
        rag_result_obj = await client.call_tool(
            "rag_tool",
            {"question": "What are the outcomes of pneumonia clinical trials?"}
        )

        if not rag_result_obj.content:
            print("No documents found in MCP.")
            return

        # Print the retrieved text
        print(rag_result_obj.content[0].text)


# Run the async test
asyncio.run(main())
