Agentic AI — Natural Language to SQL (NL → SQL)
----------------------------------------------------
Schema-Aware | Gemini LLM | LangGraph | MySQL MCP | LangSmith Observability | Dockerized Microservice

This project demonstrates a production-ready Agentic AI system that converts natural language queries into SQL commands, validates them using database schema awareness, and executes them safely through a MySQL MCP (Model Context Protocol) server — with full observability powered by LangSmith.
It is built as a containerized microservice featuring:

-Gemini LLM for NL → SQL reasoning

-LangGraph workflow for schema-based SQL generation

-MCP server for safe SQL execution

-LangSmith for tracing, debugging, cost tracking, latency insights

-Gradio UI for users to interact with the system

-Docker Compose for full deployment (including HTTPS + proxy)

 
 Features
----------------------------------------------------
 1. Natural Language → SQL Conversion
-------------------------------------

User queries like:

“Show all orders placed by user 3”
are automatically converted into valid MySQL queries.

 2. Schema-Aware Query Generation
 -------------------------------------

The workflow fetches live DB schema using MCP → passes it to LLM → prevents invalid SQL.

 3. MySQL MCP Server (Full Agentic Capability)
 -------------------------------------

AI doesn’t touch the DB directly.
MCP server handles:

schema retrieval

SQL execution

parameter validation

multi-statement support

 4. LangSmith Observability
 ------------------------------------

Every step is fully traced:

Trace Type	Shows
nl_sql_workflow	Full NL→SQL→Execution pipeline, including LLM calls
sql_execution	SQL-only MCP execution traces
Token usage	Cost tracking for Gemini
Latency	LLM vs DB timing
Errors	Debug workflow failures

5. Gradio UI
-------------------------------------

User-friendly interface to type NL queries and inspect:

generated SQL

DB results

workflow logs

6. Fully Containerized
-------------------------------------

Includes:

Nginx proxy

Let’s Encrypt SSL

Agentic AI app

MySQL MCP server

Env variable-based configuration

Architecture
----------------------------------------------------
User (Gradio UI)
        ↓
LangGraph Workflow
        ↓
Gemini LLM (SQL generation)
        ↓
MySQL MCP Server (http://agentic_app:8080)
        ↓
MySQL Database
        ↓
LangSmith (Tracing/Monitoring)

Folder Structure
----------------------------------------------------
agentic_ai_nltosql/

│── Dockerfile

│── docker-compose.yml

│── requirements.txt

│── README.md

│── app/

│     ├── gradio_agentic_ui.py

│     ├── langgraph_schema_graph.py

│     ├── mysql_mcp_server.py

│     ├── *_WORKING (backup files)

Installation & Running
----------------------------------------------------
1. Clone the repo
git clone https://github.com/mshan0181/langsmith_integration_nl2sql_ai.git
cd agentic_ai_nltosql

2. Fill .env file
GEMINI_API_KEY=your_gemini_key
LANGCHAIN_API_KEY=lsv2_sk_your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=agentic-production

# MySQL External/Host DB
DB_HOST=your-host
DB_PORT=3306
DB_USER=root
DB_PASSWORD=xxxx
DB_NAME=ai_agent_db

3. Start the system
docker-compose up -d

4. Access the Application
Component	URL
Gradio UI	http://<IP>:7860
MCP Server	http://<IP>:8080
LangSmith Dashboard	https://smith.langchain.com
Example NL Queries

Show all tables

Insert a user named Vijay with email vijay@domain.com

Add a product called Smart TV priced at 45000

Show the order placed by user 3 for product 9

Count total products in electronics category

Show dashboard summary of orders grouped by user

LangSmith Observability Screenshots
----------------------------------------------------
✔ SQL Execution Tracing

All MCP calls appear as sql_execution

Schema + statement + result included

✔ Full Workflow Traces

LLM calls

Prompt + Response

Token usage

Latency charts

✔ Error Debugging

Invalid SQL

Schema mismatches

MySQL errors (1054, 1064, etc.)

Key Components Explained
----------------------------------------------------
 1. langgraph_schema_graph.py

Handles:

schema fetching

prompt construction

LLM invocation

SQL generation

workflow orchestration

2. mysql_mcp_server.py

Safe SQL execution engine:

schema endpoint: /schema

SQL executor: /run

multi-query execution support

full LangSmith tracing inside MCP

schema snapshot return

 
 3. gradio_agentic_ui.py

Frontend that:

calls LangGraph workflow

calls MCP execution

merges response into readable JSON

Security Considerations
----------------------------------------------------

No DROP/TRUNCATE allowed

LLM prompt hardened

MCP server validates every query

Docker sandboxing


 Deployment Options
----------------------------------------------------

Cloud VM (GCP/AWS/Azure)

Docker Swarm

Kubernetes

Local development

Supports HTTPS auto-generation via Let’s Encrypt.

Roadmap
----------------------------------------------------

 Add RAG-based schema explanations

 Add Query Caching

 Add Role-Based Access Control

 Add SQL result visualization (Charts)

 Add async execution pipeline

 Add multi-DB support (Postgres, Snowflake)

 Contributing
----------------------------------------------------

Pull requests welcome!
Feel free to open issues for suggestions or bugs.
