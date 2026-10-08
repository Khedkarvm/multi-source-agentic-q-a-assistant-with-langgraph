import asyncio
from fastmcp.client import Client  

async def main():
    async with Client("http://127.0.0.1:9000/mcp") as client: 
        print("SQL TOOL TEST")

        # Correct SQL with lowercase column names
        sql_result_obj = await client.call_tool(
            "sql_query_tool",
            {"sql_query": "SELECT customer_id, company_name FROM customers LIMIT 5;"}  
        )

        # Extract text from result
        sql_result = sql_result_obj.content[0].text if sql_result_obj.content else "No result"
        print(sql_result)

asyncio.run(main())
