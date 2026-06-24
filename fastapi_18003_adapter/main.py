# -*- coding: utf-8 -*-
"""FastAPI adapter that connects chat.html to OpenClaw Gateway sessions.

This adapter is intentionally thin:
- /chat accepts browser messages and sends them to the market_strategy Agent.
- /sse streams callback/progress events to the browser.
- /callback receives ReAct events from independent Agents.

It must not implement market-analysis orchestration in Python.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any, AsyncIterator, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .gateway_client import MARKET_AGENT_ID, post_chat_completion
from .models import CallbackPayload, ChatRequest
from .session_manager import session_manager


ADAPTER_BASE_URL = os.environ.get("MARKET_WEB_ADAPTER_BASE_URL", "http://127.0.0.1:18003").rstrip("/")
HEARTBEAT_SECONDS = 15

app = FastAPI(title="Market WebChat OpenClaw Adapter", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _sse(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _event_kind(event: Dict[str, Any]) -> str:
    explicit = str(event.get("event") or event.get("type") or "").strip().lower()
    if explicit in {"progress", "react", "complete", "error"}:
        return explicit
    phase = str(event.get("phase") or "").strip().lower()
    if phase == "complete" or "report" in event or "answer" in event:
        return "complete"
    if phase == "error" or event.get("error"):
        return "error"
    return "react"


def _complete_payload(req: ChatRequest, gateway_result: Dict[str, Any], started_at: float) -> Dict[str, Any]:
    text = str(gateway_result.get("text") or "")
    return {
        "success": bool(gateway_result.get("ok")),
        "question": req.question,
        "analysis_type": req.analysis_type or "",
        "time_range": req.time_range or "",
        "confidence": 0,
        "quality_passed": bool(gateway_result.get("ok")),
        "evidence_count": 0,
        "execution_time": round(time.time() - started_at, 2),
        "sources": [f"openclaw:{MARKET_AGENT_ID}"],
        "missing_or_uncertain": [] if gateway_result.get("ok") else [gateway_result.get("error") or "Gateway call failed"],
        "report": text,
        "answer": text,
        "raw": {
            "gateway": {k: v for k, v in gateway_result.items() if k != "raw"},
            "session_id": req.session_id,
        },
    }


def build_market_agent_message(req: ChatRequest) -> str:
    callback_url = f"{ADAPTER_BASE_URL}/callback"
    payload = {
        "source": "chat.html",
        "session_id": req.session_id,
        "callback_url": callback_url,
        "user_message": req.question,
        "analysis_type": req.analysis_type,
        "time_range": req.time_range,
        "max_cycles": req.max_cycles,
        "routing_contract": {
            "ordinary_chat": "Answer in the current market_strategy OpenClaw session.",
            "complex_market_task": (
                "If analysis_type is business_analysis, opportunity_assessment, "
                "comprehensive_research, or policy_impact, call sessions_send("
                "agentId='strategy-orchestrator', ...) and pass session_id plus callback_url."
            ),
            "callback_requirement": (
                "The downstream strategy-orchestrator must POST each ReAct event to callback_url "
                "as {'session_id': session_id, 'event': {...}}. The final callback should include "
                "phase='Complete' and report or answer."
            ),
        },
    }
    return (
        "You are receiving a web chat turn from chat.html through the OpenClaw Gateway.\n"
        "Follow the routing contract exactly. Do not let the FastAPI adapter perform orchestration.\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
    )


async def _run_gateway_turn(req: ChatRequest) -> None:
    started_at = time.time()
    await session_manager.push(
        req.session_id,
        "progress",
        {
            "phase": "Gateway",
            "stage": "stage1",
            "status": "running",
            "summary": f"Sending turn to OpenClaw agent={MARKET_AGENT_ID}; session_id={req.session_id}",
        },
    )
    message = build_market_agent_message(req)
    result = await asyncio.to_thread(
        post_chat_completion,
        agent_id=MARKET_AGENT_ID,
        session_id=req.session_id,
        message=message,
    )
    if result.get("ok"):
        await session_manager.push(
            req.session_id,
            "complete",
            _complete_payload(req, result, started_at),
        )
    else:
        await session_manager.push(
            req.session_id,
            "error",
            {
                "success": False,
                "error": result.get("error") or "OpenClaw Gateway call failed",
                "execution_time": round(time.time() - started_at, 2),
                "raw": result,
            },
        )


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "mode": "openclaw_gateway_event_adapter",
        "timestamp": time.time(),
        "sessions": await session_manager.snapshot(),
    }


@app.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question cannot be empty")
    await session_manager.mark_running(req.session_id)
    await session_manager.push(
        req.session_id,
        "react",
        {
            "phase": "Accept",
            "stage": "stage0",
            "status": "done",
            "summary": "Accepted browser message; adapter will relay to OpenClaw Gateway.",
        },
    )
    asyncio.create_task(_run_gateway_turn(req))
    return {"accepted": True, "session_id": req.session_id}


@app.get("/sse")
async def sse(session_id: str) -> StreamingResponse:
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    await session_manager.get_or_create(session_id)

    async def stream() -> AsyncIterator[str]:
        while True:
            item = await session_manager.pop(session_id, timeout=HEARTBEAT_SECONDS)
            if item is None:
                yield _sse(
                    "progress",
                    {
                        "phase": "Heartbeat",
                        "stage": "heartbeat",
                        "status": "running",
                        "summary": "Waiting for OpenClaw Agent callback or final response.",
                    },
                )
                continue
            yield _sse(str(item["event"]), item["data"])
            if item["event"] in {"complete", "error"}:
                break

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


@app.post("/callback")
async def callback(payload: CallbackPayload) -> Dict[str, Any]:
    if not payload.session_id:
        raise HTTPException(status_code=400, detail="session_id is required")
    event = dict(payload.event or {})
    event.setdefault("timestamp", time.time())
    event_kind = _event_kind(event)
    if event_kind == "complete":
        event.setdefault("success", True)
        event.setdefault("quality_passed", True)
        event.setdefault("confidence", 0)
        if "report" not in event and "answer" in event:
            event["report"] = event["answer"]
    await session_manager.push(payload.session_id, event_kind, event)
    return {"ok": True, "session_id": payload.session_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("fastapi_18003_adapter.main:app", host="127.0.0.1", port=18003, reload=False)
