# super_mcp/sql_agent.py

import os
import json
import re
import asyncio
from sqlalchemy import text
from fastmcp.client import Client
from langchain_core.messages import HumanMessage
from langchain_core.tools import Tool
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv

from super_mcp.sql_tool_helpers import engine, save_schema_to_json

load_dotenv()

# load schema
def load_schema(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)

SCHEMA = load_schema("northwind_schema.json")

TABLES = {table.lower(): columns for table, columns in SCHEMA.items()}

# helper extract table
def extract_tables_from_sql(sql: str) -> list[str]:
    pattern = r"\b(?:FROM|JOIN)\s+([a-zA-Z_][a-zA-Z0-9_]*)"
    tables = re.findall(pattern, sql, re.IGNORECASE)

    tables = list({t.lower() for t in tables})
    return tables

# helper cleam llm
def clean_sql(output: str) -> str:
    return re.sub(r"<function=.*?>\{(.*)\}</function>", r"\1", output)

# helper append n question
def append_limit(sql: str, question: str) -> str:
    # Check for top N
    match = re.search(r'\btop\s+(\d+)', question, re.IGNORECASE)
    if match and 'limit' not in sql.lower():
        limit = match.group(1)
        sql = sql.rstrip(';') + f' LIMIT {limit};'
    return sql

def is_sql_error(error_msg: str) -> bool:
    keywords = [
        "syntax error",
        "does not exist",
        "undefined column",
        "relation",
        "invalid"
    ]
    return any(k in error_msg.lower() for k in keywords)


# mcp load 
async def _load_mcp_tools():
    tools_for_langchain = []
    async with Client("http://127.0.0.1:9000/mcp") as client:
        mcp_tools = await client.list_tools()
        for tool in mcp_tools:
            tool_name = tool.name
            description = tool.description or "MCP tool"
            schema = tool.inputSchema or {}
            required = schema.get("required", [])
            if not required:
                raise RuntimeError(f"MCP tool '{tool_name}' has no required input field")
            input_key = required[0]

            def make_executor(name, key, client_ref):
                def executor(input_text: str) -> str:
                    async def _call():
                        response = await client_ref.call_tool(name, {key: input_text})
                        if response.content:
                            return response.content[0].text
                        return ""
                    return asyncio.run(_call())
                return executor

            tools_for_langchain.append(
                Tool(
                    name=tool_name,
                    description=description,
                    func=make_executor(tool_name, input_key, client)
                )
            )
    return tools_for_langchain

def load_mcp_tools():
    return asyncio.run(_load_mcp_tools())


# llm
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.environ["GROQ_API_KEY"]
)


# sql prompt
SQL_PROMPT = f"""
You are a SQL generator for PostgreSQL.

DATABASE SCHEMA (tables → columns):
{json.dumps(TABLES, indent=2)}

RULES:
- Output exactly ONE SQL SELECT query
- Use ONLY table names and columns from schema
- Include LIMIT N if question asks for top N rows
- "Check the data and generate SQL only for years present in the database."
- Output SQL ONLY. No explanations.
- If unsure, output exactly:
SELECT 'INSUFFICIENT_SCHEMA' AS error;
"""


# sql agent
sql_agent = create_agent(
    model=llm,
    tools=load_mcp_tools(),
    system_prompt=SQL_PROMPT,
    name="sql_agent",
).with_config({"max_retries": 0})



def run_sql_agent(question: str) -> dict:
    sql = ""
    tables_used = []

    try:
        #  Generate SQL
        result = sql_agent.invoke({"messages": [HumanMessage(content=question)]})
        sql = result["messages"][-1].content.strip()
        sql = clean_sql(sql).rstrip(";")

        # Guard: insufficient schema
        if "INSUFFICIENT_SCHEMA" in sql:
            return {
                "status": "failed",
                "error": "Insufficient schema to answer question",
                "generated_sql": sql,
                "tables_used": [],
                "data": [],
            }

        # Append LIMIT if required
        sql = append_limit(sql, question).rstrip(";")

        # Extract tables
        tables_used = extract_tables_from_sql(sql)

        # Execute SQL
        with engine.connect() as conn:
            result_set = conn.execute(text(sql))
            rows = result_set.fetchall()
            columns = result_set.keys()

        data = [dict(zip(columns, row)) for row in rows]

        return {
            "status": "success",
            "generated_sql": sql,
            "tables_used": tables_used,
            "data": data,
        }

    except Exception as e:
        error_msg = str(e)

   
        if is_sql_error(error_msg):
            try:
                retry_prompt = f"""
The following SQL failed:
{sql}

Error:
{error_msg}

Fix the SQL using ONLY the schema.
Return ONLY SQL.
"""
                retry_result = llm.invoke([HumanMessage(content=retry_prompt)])
                fixed_sql = clean_sql(retry_result.content).rstrip(";")

                with engine.connect() as conn:
                    result_set = conn.execute(text(fixed_sql))
                    rows = result_set.fetchall()
                    columns = result_set.keys()

                data = [dict(zip(columns, row)) for row in rows]

                return {
                    "status": "success",
                    "generated_sql": fixed_sql,
                    "tables_used": extract_tables_from_sql(fixed_sql),
                    "data": data,
                }

            except Exception:
                pass

        return {
            "status": "failed",
            "error": error_msg,
            "generated_sql": sql,
            "tables_used": tables_used,
            "data": [],
        }




if __name__ == "__main__":
    question = input("Enter your question: ")
    result = run_sql_agent(question)
    print("\nGenerated SQL:\n", result["generated_sql"])
    print("\nTables used:", ", ".join(result["tables_used"]))
    print("\nQuery Result:\n", json.dumps(result["data"], indent=2))
