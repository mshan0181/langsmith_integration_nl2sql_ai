import os, json, requests
from dotenv import load_dotenv

# LangGraph
from langgraph.graph import StateGraph, START, END

# LLM (Gemini)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

# LangSmith tracing
from langsmith import traceable

# === Load environment variables ===
load_dotenv()

# URLs for MCP server
MCP_SCHEMA_URL = os.getenv("MCP_SCHEMA_URL", "http://agentic_app:8080/schema")
MCP_RUN_URL = os.getenv("MCP_RUN_URL", "http://agentic_app:8080/run")

# LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-pro")
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# === Initialize Gemini LLM ===
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    google_api_key=GOOGLE_API_KEY
)

# === Prompt Template ===
PROMPT = PromptTemplate(
    input_variables=["user_query", "schema_json"],
    template="""
You are an expert MySQL DBA.
Given the database schema and user request, generate a correct SQL query.

Schema (JSON):
{schema_json}

User request:
{user_query}

Guidelines:
- Use existing schema.
- Never include DROP DATABASE or TRUNCATE.
- Return ONLY valid MySQL SQL query.

SQL:
"""
)

# === Helper: Extract user query ===
def extract_user_query(messages):
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, dict):
        return last.get("content", "")
    if hasattr(last, "content"):
        return last.content
    return str(last)

# =====================================================================
# 🟦 Node 1 — Fetch live DB schema from MCP server
# =====================================================================
@traceable(name="fetch_schema")
def fetch_schema_node(state):
    try:
        r = requests.get(MCP_SCHEMA_URL, timeout=5)
        schema = r.json() if r.status_code == 200 else {"error": r.text}
    except Exception as e:
        schema = {"error": str(e)}

    state["schema"] = schema
    return state

# =====================================================================
# 🟩 Node 2 — Generate SQL using Gemini LLM (Fully traced)
# =====================================================================
@traceable(name="llm_sql_generation")
def generate_sql_node(state):
    user_query = extract_user_query(state.get("messages", []))
    schema_json = json.dumps(state.get("schema", {}), default=str)[:4000]

    try:
        sql_resp = llm.invoke(
            PROMPT.format(
                user_query=user_query,
                schema_json=schema_json
            )
        )
        sql = sql_resp.content.strip()
    except Exception as e:
        sql = f"-- SQL generation failed: {e}"

    state["user_query"] = user_query
    state["sql"] = sql
    return state

# =====================================================================
# 🟧 Node 3 — Execute SQL via MCP server (Fully traced)
# =====================================================================
@traceable(name="sql_execution")
def execute_sql_node(state):
    sql = state.get("sql")

    if not sql or sql.startswith("-- SQL generation failed"):
        state["response"] = {"error": "No valid SQL to execute"}
        return state

    try:
        r = requests.post(
            MCP_RUN_URL,
            json={"query": sql, "dry_run": False},
            timeout=15
        )

        if r.status_code == 200:
            response = r.json()
        else:
            response = {"error": r.text}

    except Exception as e:
        response = {"error": str(e)}

    state["response"] = response
    return state

# =====================================================================
# 🧠 LangGraph Pipeline  
# =====================================================================
graph = StateGraph(dict)

graph.add_node("fetch_schema", fetch_schema_node)
graph.add_node("generate_sql", generate_sql_node)
graph.add_node("execute_sql", execute_sql_node)

graph.add_edge(START, "fetch_schema")
graph.add_edge("fetch_schema", "generate_sql")
graph.add_edge("generate_sql", "execute_sql")
graph.add_edge("execute_sql", END)

compiled_graph = graph.compile()

# =====================================================================
# 🚀 External Entry Point
# =====================================================================
@traceable(name="nl_sql_workflow")
def run_schema_validation_workflow(user_text: str):
    state = {"messages": [{"role": "user", "content": user_text}]}
    result = compiled_graph.invoke(state)

    if hasattr(result, "state"):
        result = result.state  # unwrap PregelOutput

    return {
        "user_query": result.get("user_query"),
        "sql": result.get("sql"),
        "response": result.get("response"),
        "schema": result.get("schema"),
    }


# Standalone test
if __name__ == "__main__":
    print(json.dumps(
        run_schema_validation_workflow("Show all tables"),
        indent=2
    ))
