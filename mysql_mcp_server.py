import os
import json
import re
import mysql.connector
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

# ===========================
# 🔧 Load environment config
# ===========================
load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "testdb")

# ===========================
# 🔍 LangSmith Integration
# ===========================
from langsmith import Client, traceable, tracing_context

try:
    ls_client = Client(api_key=os.getenv("LANGCHAIN_API_KEY"))
    print("✅ LangSmith tracing enabled in MCP server.")
except Exception as e:
    print(f"⚠️ LangSmith initialization failed: {e}")

# ===========================
# 🌐 FastAPI Server
# ===========================
app = FastAPI(title="Agentic MySQL MCP Server")

# Allow CORS (for Gradio UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===========================
# 🧩 Utility Functions
# ===========================

def ensure_database_exists():
    """Ensure the target database exists before connecting."""
    try:
        conn = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cur = conn.cursor()
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`")
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Verified or created database: {MYSQL_DATABASE}")
    except Exception as e:
        print(f"❌ Database creation failed: {e}")


def get_connection():
    """Return a new MySQL connection (after verifying DB)."""
    ensure_database_exists()
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE
    )


def get_schema_snapshot():
    """Return all table schemas from the connected database."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SHOW TABLES;")
        tables = [t[0] for t in cur.fetchall()]

        schema = {}
        for table in tables:
            cur.execute(f"DESCRIBE `{table}`;")
            schema[table] = cur.fetchall()

        cur.close()
        conn.close()
        return schema
    except Exception as e:
        return {"error": str(e)}


def clean_sql(sql: str) -> str:
    """Remove LLM Markdown code fences and extra spaces."""
    sql = re.sub(r"```(?:sql)?", "", sql)
    return sql.strip()


# ===========================
# 🧠 LangSmith-Traced SQL Execution
# ===========================

@traceable(name="sql_execution")
def execute_statement(cursor, stmt: str):
    """Execute a single SQL statement with LangSmith tracing."""
    cursor.execute(stmt)

    if stmt.lower().startswith(("select", "show", "describe", "explain")):
        rows = cursor.fetchall()
        return {
            "statement": stmt,
            "type": "SELECT",
            "rows": len(rows),
            "data": rows
        }

    return {
        "statement": stmt,
        "type": "WRITE",
        "rows_affected": cursor.rowcount
    }


# ===========================
# ⚙️ API Endpoints
# ===========================

@app.get("/")
def root():
    return {"status": "MCP server running", "database": MYSQL_DATABASE}


@app.get("/schema")
def get_schema():
    """Return the live schema snapshot."""
    return get_schema_snapshot()


@app.post("/run")
async def run_sql(request: Request):
    """Execute an SQL query, returning results and schema."""

    # 🔍 Trace entire request
    with tracing_context(tags=["api", "sql-run-endpoint"]):

        try:
            data = await request.json()
            query = data.get("query", "")
            dry_run = data.get("dry_run", False)

            query = clean_sql(query)
            if not query:
                return {"error": "Empty SQL query."}

            conn = get_connection()
            cur = conn.cursor()

            if dry_run:
                return {"dry_run_query": query}

            # Support multiple statements
            stmts = [s.strip() for s in query.split(";") if s.strip()]
            responses = []

            for stmt in stmts:
                try:
                    # 🔍 Trace individual SQL statements
                    with tracing_context(
                        tags=["sql-statement"],
                        metadata={"statement": stmt}
                    ):
                        result = execute_statement(cur, stmt)

                        if result["type"] == "WRITE":
                            conn.commit()

                        responses.append(result)

                except mysql.connector.Error as e:
                    responses.append({
                        "statement": stmt,
                        "type": "ERROR",
                        "error": str(e),
                    })

            cur.close()
            conn.close()

            return {
                "status": "success",
                "results": responses,
                "schema": get_schema_snapshot()
            }

        except Exception as e:
            return {"error": str(e)}
