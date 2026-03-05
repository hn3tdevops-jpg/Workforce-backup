"""
Developer console routes — superadmin only.
GET  /console/           → serves the console HTML UI
POST /console/execute    → executes Python or shell code, returns JSON
GET  /console/copilot    → serves the Copilot chat UI
POST /console/copilot/chat → proxies to an OpenAI-compatible AI API
"""
import io
import json as _json
import os
import subprocess
import sys
import traceback

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.core.auth_deps import SuperAdmin

router = APIRouter(prefix="/console", tags=["console"])

_templates_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "templates")
templates = Jinja2Templates(directory=os.path.abspath(_templates_dir))

# Persistent Python namespace across requests in the same process
_console_namespace: dict = {}

# Max bytes returned per execution to prevent session termination
_MAX_OUTPUT_BYTES = 10_000


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def console_ui(request: Request):
    """Serve the console HTML page (auth enforced client-side via JWT)."""
    return templates.TemplateResponse("console.html", {"request": request})


class ExecutePayload(BaseModel):
    code: str
    mode: str = "python"  # "python" or "shell"


@router.post("/execute")
def console_execute(
    payload: ExecutePayload,
    _superadmin: SuperAdmin,
):
    """Execute code and return output. Requires superadmin JWT."""
    output = ""
    error = ""

    if payload.mode == "shell":
        try:
            result = subprocess.run(
                payload.code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout
            error = result.stderr
        except subprocess.TimeoutExpired:
            error = "Command timed out after 30 seconds."
        except Exception as exc:
            error = str(exc)
    else:
        stdout_cap = io.StringIO()
        stderr_cap = io.StringIO()
        old_out, old_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = stdout_cap, stderr_cap
        try:
            exec(compile(payload.code, "<console>", "exec"), _console_namespace)  # noqa: S102
        except Exception:
            error = traceback.format_exc()
        finally:
            sys.stdout, sys.stderr = old_out, old_err
        output = stdout_cap.getvalue()
        if not error:
            error = stderr_cap.getvalue()

    def _truncate(s: str) -> str:
        if len(s) > _MAX_OUTPUT_BYTES:
            return s[:_MAX_OUTPUT_BYTES] + f"\n… [truncated – {len(s) - _MAX_OUTPUT_BYTES} bytes omitted]"
        return s

    return {"output": _truncate(output), "error": _truncate(error)}


@router.post("/reset", status_code=204, include_in_schema=False)
def console_reset(_superadmin: SuperAdmin):
    """Clear the persistent console namespace (reset session state)."""
    _console_namespace.clear()


# ── Copilot chat ─────────────────────────────────────────────────────────────

_COPILOT_API_BASE = os.getenv("COPILOT_API_BASE", "https://api.openai.com/v1")
_COPILOT_API_KEY  = os.getenv("COPILOT_API_KEY", "")
_COPILOT_MODEL    = os.getenv("COPILOT_MODEL", "gpt-4o")


@router.get("/copilot", response_class=HTMLResponse, include_in_schema=False)
def copilot_ui(request: Request):
    """Serve the Copilot chat UI (auth enforced client-side via JWT)."""
    return templates.TemplateResponse("copilot.html", {"request": request})


class CopilotMessage(BaseModel):
    role: str   # "user" | "assistant" | "system"
    content: str


class CopilotChatPayload(BaseModel):
    messages: list[CopilotMessage]


@router.post("/copilot/chat", include_in_schema=False)
async def copilot_chat(
    payload: CopilotChatPayload,
    _superadmin: SuperAdmin,
):
    """Stream a Copilot response. Requires superadmin JWT."""
    if not _COPILOT_API_KEY:
        return {"error": "COPILOT_API_KEY is not configured on the server."}

    system_msg = {
        "role": "system",
        "content": (
            "You are GitHub Copilot, an AI assistant embedded in the Workforce "
            "scheduling platform developer console. Help the operator understand "
            "the codebase, debug issues, write code, and manage the system. "
            "Be concise and technical."
        ),
    }
    messages = [system_msg] + [m.model_dump() for m in payload.messages]

    async def event_stream():
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                async with client.stream(
                    "POST",
                    f"{_COPILOT_API_BASE}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {_COPILOT_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={"model": _COPILOT_MODEL, "messages": messages, "stream": True},
                ) as resp:
                    if resp.status_code != 200:
                        body = await resp.aread()
                        yield f"data: {_json.dumps({'error': body.decode()})}\n\n"
                        return
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]
                            if chunk.strip() == "[DONE]":
                                yield "data: [DONE]\n\n"
                                return
                            try:
                                delta = _json.loads(chunk)
                                text = (
                                    delta.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content", "")
                                )
                                if text:
                                    yield f"data: {_json.dumps({'text': text})}\n\n"
                            except Exception:
                                pass
        except Exception as exc:
            yield f"data: {_json.dumps({'error': str(exc)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
