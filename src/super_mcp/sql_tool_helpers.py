# super_mcp/sql_tool_helpers.py

import json
import re
import warnings
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SAWarning
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

# ---------------------------
# Setup
# ---------------------------
warnings.filterwarnings("ignore", category=SAWarning)
load_dotenv()

# ---------------------------
# Database connection
# ---------------------------
DB_URL = "postgresql+psycopg2://postgres:9767@localhost:5433/northwind"
engine = create_engine(DB_URL)

# ---------------------------
# Save schema to JSON
# ---------------------------
def save_schema_to_json(engine, json_path="northwind_schema.json"):
    inspector = inspect(engine)
    metadata = {}
    for table in inspector.get_table_names():
        cols = inspector.get_columns(table)
        metadata[table] = [c["name"] for c in cols]

    with open(json_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Schema saved to {json_path}")
    return metadata

SCHEMA = save_schema_to_json(engine)

# ---------------------------
# Initialize LLM
# ---------------------------
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0,
    groq_api_key=os.environ.get("GROQ_API_KEY")
)

# ---------------------------
# Prompt template (includes top N rules)
# ---------------------------
tables_description = "\n".join(
    f"{table}: {', '.join(columns)}"
    for table, columns in SCHEMA.items()
)

prompt = PromptTemplate(
    input_variables=["question"],
    template=f"""
You are an expert PostgreSQL SQL generator.

Database schema:
{tables_description}

RULES:
- Use only the tables and columns above
- Return only one SQL SELECT query
- If the question asks for 'top N products', sort by the quantity available (units_in_stock) DESC and add LIMIT N
- Do NOT add explanations, markdown, or any other text
- Only SELECT queries are allowed

Question: {{question}}

SQL:
"""
)

chain = prompt | llm | StrOutputParser()

# ---------------------------
# Generate SQL
# ---------------------------
def generate_sql_from_question(question: str) -> str:
    sql_query = chain.invoke({"question": question}).strip()
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    if not sql_query.lower().startswith("select"):
        raise ValueError("Only SELECT queries are allowed")

    # Auto-fix known column names
    sql_query = re.sub(r'\bcustomer_name\b', 'company_name', sql_query, flags=re.IGNORECASE)
    
    return sql_query

# ---------------------------
# Execute SQL and return table string
# ---------------------------
def run_sql_query(sql_query: str) -> str:
    with engine.connect() as conn:
        result = conn.execute(text(sql_query))
        rows = result.fetchall()
        columns = result.keys()

        if rows:
            table_str = "\t".join(columns) + "\n"
            for row in rows:
                table_str += "\t".join(str(x) for x in row) + "\n"
        else:
            table_str = "No results found."

    return table_str

# ---------------------------
# Test block
# ---------------------------
if __name__ == "__main__":
    test_question = "list customer from germany"
    try:
        sql = generate_sql_from_question(test_question)
        print("Generated SQL:\n", sql)

        result = run_sql_query(sql)
        print("\nQuery Result:\n", result)
    except Exception as e:
        print("Error:", e)
