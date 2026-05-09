from __future__ import annotations

import asyncio
import os
import sys
from collections.abc import Awaitable, Callable
from importlib import import_module
from typing import Any

from dotenv import load_dotenv
from pydantic import ValidationError

from app.mock_agent import run_agent_adapter as run_mock_agent_adapter
from app.models import ProfileData

StatusCallback = Callable[[str, str], Awaitable[None]]
LeadCallback = Callable[[ProfileData], Awaitable[None]]

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
load_dotenv(os.path.join(ROOT_DIR, ".env"))
load_dotenv()
load_dotenv(os.path.join(ROOT_DIR, "agent", ".env"))


def _infer_step(message: str) -> str:
    lowered = message.lower()
    if "analyzing" in lowered or "extract" in lowered:
        return "extracting"
    if "score" in lowered:
        return "scoring"
    if "initializing" in lowered or "starting" in lowered or "browser" in lowered:
        return "browsing"
    return "browsing"


async def run_agent_adapter(
    handles: list[str],
    on_status: StatusCallback,
    on_lead: LeadCallback,
) -> None:
    if os.getenv("USE_MOCK_AGENT", "auto").lower() in {"1", "true", "yes", "on"}:
        await run_mock_agent_adapter(handles, on_status, on_lead)
        return

    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)

    try:
        agent = import_module("agent")
        run_agent_async = getattr(agent, "run_agent_async")
        agent_config = getattr(agent, "AgentConfig")(max_profiles=10, timeout_seconds=180)
    except Exception:
        if os.getenv("USE_MOCK_AGENT", "auto").lower() in {"0", "false", "no", "off"}:
            raise
        await run_mock_agent_adapter(handles, on_status, on_lead)
        return

    pending_tasks: list[asyncio.Task[Any]] = []

    def status_callback(message: str) -> None:
        pending_tasks.append(asyncio.create_task(on_status(message, _infer_step(message))))

    def lead_callback(raw_lead: dict[str, Any]) -> None:
        try:
            profile = ProfileData.model_validate(raw_lead)
        except ValidationError as exc:
            pending_tasks.append(
                asyncio.create_task(
                    on_status(f"Skipping malformed lead from agent: {exc.errors()[0]['msg']}", "extracting")
                )
            )
            return
        pending_tasks.append(asyncio.create_task(on_lead(profile)))

    await run_agent_async(
        handles=handles,
        on_status=status_callback,
        on_lead=lead_callback,
        config=agent_config,
    )

    if pending_tasks:
        await asyncio.gather(*pending_tasks)
