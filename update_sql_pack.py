import pathlib

# Read the current file
target = pathlib.Path(r"C:\\Users\\11489\\.openclaw\\workspace-data-agent\\agents\\strategy-orchestrator\\tools\\targeted_sql_pack.py")
content = target.read_text("utf-8")

# Add callback constants after RAG_ENGINE_ROOT
old_rag = '''RAG_ENGINE_ROOT = Path(r"E:\\AI\\data\\envs\\car_agent_env\\ai-decision\\rag-engine")
if str(RAG_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_ROOT))'''

new_rag = '''RAG_ENGINE_ROOT = Path(r"E:\\AI\\data\\envs\\car_agent_env\\ai-decision\\rag-engine")
if str(RAG_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(RAG_ENGINE_ROOT))

EXPECTED_PYTHON = Path(r"E:\\AI\\data\\envs\\car_agent_env\\Scripts\\python.exe")
CALLBACK_CLIENT_PATH = Path(r"C:\\Users\\11489\\.openclaw\\workspace-market\\fastapi_18003_adapter\\callback_client.py")
CALLBACK_URL = "http://127.0.0.1:18003/callback"

def _emit_callback(session_id: str, phase: str, status: str, summary: str, agent: str = "data-agent") -> None:
    if not session_id:
        return
    import subprocess
    cmd = [
        str(EXPECTED_PYTHON),
        str(CALLBACK_CLIENT_PATH),
        "--session-id", session_id,
        "--callback-url", CALLBACK_URL,
        "--phase", phase,
        "--status", status,
        "--agent", agent,
        "--summary", summary,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception:
        pass'''

if old_rag in content:
    content = content.replace(old_rag, new_rag)
    print("Added callback constants and _emit_callback")
else:
    print("Could not find RAG_ENGINE_ROOT block")

# Modify run_targeted_sql_pack signature
old_sig = "def run_targeted_sql_pack(\n    analysis_plan: Any,\n    connection_factory: Optional[Callable[[], Any]] = None,\n) -> Dict[str, Any]:"
new_sig = "def run_targeted_sql_pack(\n    analysis_plan: Any,\n    connection_factory: Optional[Callable[[], Any]] = None,\n    session_id: Optional[str] = None,\n    callback_url: Optional[str] = None,\n) -> Dict[str, Any]:"

if old_sig in content:
    content = content.replace(old_sig, new_sig)
    print("Modified run_targeted_sql_pack signature")
else:
    print("Could not find run_targeted_sql_pack signature")

# Add callback at start of function (after plan = _plan_to_dict)
old_plan = "plan = _plan_to_dict(analysis_plan)\n\n    conn = None"
new_plan = """plan = _plan_to_dict(analysis_plan)

    if session_id:
        _emit_callback(session_id, "DataRunning", "running", "data-agent retrieving data")

    conn = None"""

if "plan = _plan_to_dict(analysis_plan)" in content and "conn = None" in content:
    content = content.replace("plan = _plan_to_dict(analysis_plan)\n\n    conn = None", new_plan)
    print("Added callback at start")
else:
    print("Could not find plan assignment")

target.write_text(content, "utf-8")
print("File updated successfully")
