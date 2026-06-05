"""
FastAPI application interface for the ExecSuite.ai dashboard,
handling real-time updates via Server-Sent Events (SSE).
"""

import asyncio
import json
import logging
import os
import threading
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from core.llm_wrapper import LLMWrapper
from core.memory import SharedMemory
from core.organization import DEPARTMENTS, Organization

# Load env variables
load_dotenv()

logger = logging.getLogger(__name__)

app = FastAPI(title="ExecSuite.ai - Multi-Department Dashboard")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Shared Memory and Organization
# We store the workspace in the absolute path of './workspace'
workspace_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "workspace"))
memory = SharedMemory(workspace_dir=workspace_path)
org = Organization(memory=memory)

# Active SSE client queues
sse_clients: List[asyncio.Queue] = []
SSE_LOOP: Optional[asyncio.AbstractEventLoop] = None


def broadcast_event(event: Dict[str, Any]) -> None:
    """
    Push memory updates to all connected SSE clients.

    Args:
        event: The event payload dictionary.
    """
    if not sse_clients:
        return

    # Helper to push to the client queues in the main thread/event loop
    async def push_to_queues() -> None:
        for queue in sse_clients:
            await queue.put(event)

    if SSE_LOOP:
        asyncio.run_coroutine_threadsafe(push_to_queues(), SSE_LOOP)


# Register memory callback to broadcast events in real-time
memory.register_callback(broadcast_event)


# Data Models
class TaskRequest(BaseModel):
    """API request model for executing a task."""
    task: str
    workflow: str = "collaborative"  # collaborative or sequential
    department: str = "c_suite"
    provider: Optional[str] = None
    model: Optional[str] = None


class ConfigRequest(BaseModel):
    """API request model for updating model configurations."""
    gemini_key: Optional[str] = None
    groq_key: Optional[str] = None
    openrouter_key: Optional[str] = None
    cohere_key: Optional[str] = None
    openai_key: Optional[str] = None
    default_provider: Optional[str] = None
    default_model: Optional[str] = None
    default_department: Optional[str] = None


@app.get("/api/state")
def get_state() -> Dict[str, Any]:
    """Retrieve the current state of the organization (messages, logs, files, keys, departments)."""
    # Check which keys are set
    keys_configured = {
        "gemini": bool(os.getenv("GEMINI_API_KEY") or org.llm.keys.get("gemini")),
        "groq": bool(os.getenv("GROQ_API_KEY") or org.llm.keys.get("groq")),
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY") or org.llm.keys.get("openrouter")),
        "cohere": bool(os.getenv("COHERE_API_KEY") or org.llm.keys.get("cohere")),
        "openai": bool(os.getenv("OPENAI_API_KEY") or org.llm.keys.get("openai"))
    }

    active_agents = [
        {"role_id": k, "name": v.name, "role": v.role}
        for k, v in org.agents.items()
    ]

    return {
        "messages": memory.get_messages(),
        "logs": memory.logs,
        "files": memory.list_files(),
        "is_running": org.is_running,
        "keys_configured": keys_configured,
        "current_provider": org.llm.provider,
        "current_model": org.llm.model,
        "active_department": org.department,
        "active_agents": active_agents,
        "available_departments": {k: v["name"] for k, v in DEPARTMENTS.items()}
    }


@app.post("/api/config")
def update_config(config: ConfigRequest) -> Dict[str, Any]:
    """Dynamically update API keys and LLM settings."""
    if config.gemini_key is not None:
        os.environ["GEMINI_API_KEY"] = config.gemini_key
    if config.groq_key is not None:
        os.environ["GROQ_API_KEY"] = config.groq_key
    if config.openrouter_key is not None:
        os.environ["OPENROUTER_API_KEY"] = config.openrouter_key
    if config.cohere_key is not None:
        os.environ["COHERE_API_KEY"] = config.cohere_key
    if config.openai_key is not None:
        os.environ["OPENAI_API_KEY"] = config.openai_key

    # Re-initialize LLM with new keys/provider
    provider = config.default_provider or org.llm.provider
    model = config.default_model

    org.llm = LLMWrapper(provider=provider, model=model)

    # Determine department to set
    dept = config.default_department or org.department
    org.setup_default_agents(department=dept)

    logger.info(f"[CONFIG_UPDATED] Provider: {org.llm.provider} | Model: {org.llm.model} | Dept: {org.department}")
    return {"status": "success", "provider": org.llm.provider, "model": org.llm.model}


def execute_task_thread(task: str, workflow: str) -> None:
    """
    Target function to run the organization in a background thread.

    Args:
        task: Description of the task to run.
        workflow: Workflow type identifier.
    """
    try:
        org.run_task(task, workflow)
    except Exception as ex:  # pylint: disable=broad-exception-caught
        logger.error(f"[BACKGROUND_TASK_ERROR] Error: {ex}")


@app.post("/api/run")
def start_task(req: TaskRequest) -> Dict[str, Any]:
    """Start an agentic task in the background."""
    if org.is_running:
        raise HTTPException(status_code=400, detail="A task is already executing.")

    # Apply temp provider overrides if specified
    if req.provider:
        org.llm.provider = req.provider
        if req.model:
            org.llm.model = req.model

    # Configure active department
    org.setup_default_agents(department=req.department)

    # Clear previous messages
    memory.clear()

    # Start thread
    thread = threading.Thread(target=execute_task_thread, args=(req.task, req.workflow))
    thread.daemon = True
    thread.start()

    logger.info(f"[TASK_THREAD_STARTED] Task: {req.task} | Workflow: {req.workflow} | Dept: {req.department}")
    return {"status": "started"}


@app.get("/api/files/read")
def read_file(path: str = Query(..., description="Relative path of file in workspace")) -> Dict[str, Any]:
    """Read file content from workspace."""
    try:
        content = memory.read_file(path)
        return {"content": content}
    except FileNotFoundError as ex:
        raise HTTPException(status_code=404, detail=str(ex)) from ex
    except PermissionError as ex:
        raise HTTPException(status_code=403, detail=str(ex)) from ex
    except Exception as ex:
        raise HTTPException(status_code=500, detail=str(ex)) from ex


@app.get("/api/stream")
async def event_stream() -> StreamingResponse:
    """SSE endpoint for streaming agent logs and updates in real-time."""
    global SSE_LOOP  # pylint: disable=global-statement
    if not SSE_LOOP:
        SSE_LOOP = asyncio.get_event_loop()

    queue: asyncio.Queue = asyncio.Queue()
    sse_clients.append(queue)
    logger.info(f"[SSE_CLIENT_CONNECTED] Total clients: {len(sse_clients)}")

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            # Yield connection established
            yield f"data: {json.dumps({'event': 'connected', 'data': {}})}\n\n"

            while True:
                # Wait for new events in queue
                event = await queue.get()
                yield f"data: {json.dumps(event)}\n\n"
        except asyncio.CancelledError:
            logger.info("[SSE_CLIENT_DISCONNECTED]")
        finally:
            sse_clients.remove(queue)
            logger.info(f"[SSE_CLIENT_REMOVED] Total clients: {len(sse_clients)}")

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Mount static files folder pointing to frontend directory
static_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
os.makedirs(static_path, exist_ok=True)
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
