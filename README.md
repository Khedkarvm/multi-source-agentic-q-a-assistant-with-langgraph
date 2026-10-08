# Multi-Source Agentic Q&A Assistant

A multi-agent AI system that intelligently routes user questions to specialized agents and retrieves information from multiple sources, including structured databases and biomedical documents.

The system uses **LangGraph** for agent orchestration and combines SQL-based data analysis with Retrieval-Augmented Generation (RAG) to answer different types of user queries.

## Overview

Traditional AI assistants are often designed for a single source of information. This project uses a multi-agent architecture where different agents are responsible for different tasks.

The system includes:

* A **Supervisor Agent** for query routing
* A **SQL Agent** for structured database queries
* A **RAG Agent** for document-based questions
* Shared workflow state and conversation history
* Guardrails for safer query processing
* Source-aware responses

This allows the assistant to determine which specialized agent is best suited to answer a user's question.

---

## Key Features

* Multi-agent query routing
* LangGraph-based agent orchestration
* SQL-based question answering
* Retrieval-Augmented Generation
* Multi-source information retrieval
* PostgreSQL database integration
* Biomedical document retrieval
* MCP-based tool integration
* Conversation state and history
* SQL safety validation
* Source-aware responses
* Error handling and agent workflow control

---

## System Architecture

```text
                         USER
                           ↓
                    USER QUESTION
                           ↓
                  SUPERVISOR AGENT
                           ↓
              ┌────────────┴────────────┐
              ↓                         ↓
          SQL AGENT                  RAG AGENT
              ↓                         ↓
       PostgreSQL Database       Biomedical Documents
              ↓                         ↓
       Structured Data          ChromaDB Retrieval
              └────────────┬────────────┘
                           ↓
                    RESPONSE AGENT
                           ↓
                  FINAL ANSWER
```

---

## How It Works

### 1. User Query

The user enters a question in natural language.

For example:

```text
What is the total revenue from the database?
```

or:

```text
What are the eligibility criteria for the clinical trial?
```

### 2. Supervisor Agent

The Supervisor Agent analyzes the question and determines which specialized agent should handle it.

```text
Business / SQL Question
        ↓
    SQL Agent

Document / Biomedical Question
        ↓
    RAG Agent
```

This prevents every query from being handled by the same pipeline.

### 3. SQL Agent

The SQL Agent handles questions related to structured data.

It:

* Understands the user question
* Generates SQL
* Validates the query
* Executes the query
* Handles database errors
* Returns structured results

The SQL Agent connects to PostgreSQL through the available tools.

### 4. RAG Agent

The RAG Agent handles questions related to biomedical documents.

It:

* Converts the question into an embedding
* Searches the vector database
* Retrieves relevant document chunks
* Provides the retrieved context to the LLM
* Generates an answer based on the retrieved information
* Returns relevant source information

### 5. Response Agent

The Response Agent receives the result from the selected agent and produces the final user-facing response.

This separates **information retrieval** from **final response generation**.

---

## LangGraph Workflow

The project uses LangGraph to control the multi-agent workflow.

```text
START
  ↓
Supervisor
  ↓
 ┌───────────────┐
 ↓               ↓
SQL Agent      RAG Agent
 ↓               ↓
SQL Tool       Retrieval Tool
 ↓               ↓
 └───────┬───────┘
         ↓
 Response Agent
         ↓
       END
```

The workflow maintains shared state between nodes so that information can be passed through the agent pipeline.

---

## Multi-Source Architecture

The assistant works with two major types of information sources.

### Structured Data

```text
User Question
     ↓
SQL Agent
     ↓
PostgreSQL
     ↓
SQL Result
```

### Unstructured Data

```text
User Question
     ↓
RAG Agent
     ↓
Vector Database
     ↓
Relevant Documents
     ↓
LLM Response
```

The Supervisor Agent determines which source is appropriate for the question.

---

## MCP Integration

The project uses **Model Context Protocol (MCP)** to expose tools that agents can use to interact with external resources.

Example architecture:

```text
                LangGraph
                    ↓
              Supervisor
               ↙       ↘
          SQL Agent    RAG Agent
              ↓            ↓
           MCP SQL      MCP RAG
             Tool         Tool
              ↓            ↓
        PostgreSQL     Vector Store
```

The development setup uses separate MCP services for SQL and RAG operations.

---

## Conversation State and Memory

The system maintains workflow state and conversation history so that information can be preserved across the agent execution process.

Conversation history is stored locally during development.

Example:

```text
User Question
      ↓
Agent Decision
      ↓
Tool Result
      ↓
Response
      ↓
Conversation History
```

This allows the workflow to maintain context between interactions.

---

## Guardrails

Because LLMs can generate incorrect or unsafe operations, the project includes validation mechanisms.

For SQL-based operations:

* SQL validation
* Read-only query restrictions
* Database error handling
* Controlled tool execution

For agent routing:

* Specialized agent selection
* Controlled workflow transitions
* Tool-specific responsibilities

These mechanisms help reduce incorrect tool usage and unsafe operations.

---

## Example Queries

### SQL Agent

```text
What is the total revenue?

Which category generated the highest revenue?

How many orders are there?

What is the average order value?
```

### RAG Agent

```text
What is the purpose of this clinical trial?

What are the eligibility criteria?

What treatment is being studied?

What are the study outcomes?
```

The Supervisor Agent determines which agent should process each question.

---

## Example Workflow

### Query

```text
What is the total revenue?
```

```text
User
 ↓
Supervisor Agent
 ↓
SQL Agent
 ↓
PostgreSQL
 ↓
SQL Result
 ↓
Response Agent
 ↓
Final Answer
```

### Query

```text
What are the eligibility criteria for the clinical trial?
```

```text
User
 ↓
Supervisor Agent
 ↓
RAG Agent
 ↓
Vector Database
 ↓
Relevant Document Chunks
 ↓
Response Agent
 ↓
Final Answer + Sources
```

---

## Technology Stack

| Category            | Technologies                   |
| ------------------- | ------------------------------ |
| Programming         | Python                         |
| Agent Framework     | LangGraph                      |
| LLM Framework       | LangChain                      |
| LLM                 | Large Language Models          |
| Agent Communication | MCP                            |
| Structured Data     | PostgreSQL                     |
| RAG                 | Retrieval-Augmented Generation |
| Vector Database     | ChromaDB                       |
| Embeddings          | Sentence Transformers          |
| Database Access     | SQLAlchemy                     |
| Interface           | Streamlit / Gradio             |
| Development         | VS Code, Jupyter Notebook      |
| Version Control     | Git, GitHub                    |

---

## Project Structure

```text
Multi-Agent-QA-Assistant/
│
├── src/
│   ├── agents/
│   │   ├── supervisor.py
│   │   ├── sql_agent.py
│   │   ├── rag_agent.py
│   │   └── response_agent.py
│   │
│   ├── tools/
│   │   ├── sql_tools.py
│   │   └── rag_tools.py
│   │
│   ├── mcp/
│   │   ├── sql_server.py
│   │   └── rag_server.py
│   │
│   └── workflow.py
│
├── data/
├── notebooks/
├── chat_history.json
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

> Update the structure if your actual project uses different file names or folders.

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Multi-Agent-QA-Assistant
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

### 3. Activate the environment

**Windows:**

```bash
venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Create a `.env` file with the required API keys and database configuration.

Example:

```env
DB_HOST=localhost
DB_PORT=5433
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password

LLM_API_KEY=your_api_key
```

Do not commit `.env` or API keys to GitHub.

---

## Running the Project

The project requires the relevant database and MCP services to be running before starting the main application.

The development setup uses separate services for:

```text
SQL MCP Server → Port 9000
RAG MCP Server → Port 9001
```

Start the required services and then run the main application according to the project's entry point.

---

## Key Learning

Through this project, I worked with:

* Multi-agent AI architecture
* LangGraph workflow orchestration
* Supervisor-based agent routing
* Retrieval-Augmented Generation
* Natural language to SQL
* PostgreSQL integration
* MCP tool integration
* Shared agent state
* Conversation history
* LLM tool calling
* Agent guardrails
* Multi-source question answering

---

## Future Improvements

* Add more specialized agents
* Add additional data sources
* Improve agent routing accuracy
* Add long-term memory
* Add automatic source ranking
* Improve agent evaluation
* Add observability and tracing
* Add automated testing for agent workflows

---

## Author

**Vaishnavi Khedkar**

M.Sc. Industrial Mathematics with Computer Applications

Interested in **AI/ML, Generative AI, LLMs, RAG, AI Agents, and Data Science**.
