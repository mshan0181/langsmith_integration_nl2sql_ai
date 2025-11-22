import os
import json
import requests
import gradio as gr
from langgraph_schema_graph import run_schema_validation_workflow

# =====================================================================
#  Disable LangSmith tracing ONLY for UI (MCP server handles tracing)
# =====================================================================
#############os.environ["LANGCHAIN_TRACING_V2"] = "false"
print("⚠️ LangSmith tracing disabled for Gradio UI.")

# =====================================================================
#  Main NL → SQL → MySQL pipeline
# =====================================================================
def handle(user_input):
    """
    1. Send NL query to LangGraph workflow
    2. Get the generated SQL
    3. Execute SQL using MCP server (/run)
    4. Return SQL + DB result together
    """

    # Step 1 — LLM/Workflow generates SQL
    workflow_state = run_schema_validation_workflow(user_input)

    try:
        generated_sql = workflow_state.get("sql_query", "") or workflow_state.get("sql", "")
    except:
        generated_sql = ""

    if not generated_sql:
        return "❌ Failed to generate SQL.\n\n" + json.dumps(workflow_state, indent=2, default=str)

    # Step 2 — Send SQL to MCP server
    try:
        resp = requests.post(
            "http://localhost:8080/run",
            json={"query": generated_sql}
        )
        db_result = resp.json()
    except Exception as e:
        db_result = {"error": str(e)}

    # Step 3 — Combined response
    final_output = {
        "generated_sql": generated_sql,
        "db_response": db_result
    }

    return json.dumps(final_output, indent=2, default=str)


# =====================================================================
#  Gradio UI
# =====================================================================
with gr.Blocks(title="Agentic AI for MySQL") as demo:
    gr.Markdown("# 🤖 Agentic MySQL AI (Schema-Aware)")
    inp = gr.Textbox(label="Enter your natural language query:")
    out = gr.Textbox(label="AI Generated SQL & Results", lines=20)

    btn = gr.Button("🚀 Run")
    btn.click(fn=handle, inputs=inp, outputs=out)

# =====================================================================
#  Launch Gradio on the same port exposed in Docker
# =====================================================================
demo.launch(server_name="0.0.0.0", server_port=7860)
