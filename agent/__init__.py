"""
PodPipe Agent - Twitter guest discovery using AI vision.

This module provides the agent core for browsing Twitter and extracting
potential podcast guest profiles using Northstar CUA (Computer Use Agent)
and KERNEL cloud browsers.

Usage:
    from agent import run_agent, AgentConfig

    def handle_status(msg):
        print(f"[STATUS] {msg}")

    def handle_lead(lead):
        print(f"[LEAD] {lead['name']} - {lead['twitter_handle']}")

    # Person B provides handles from LLM suggestions
    handles = ["@levelsio", "@marckohlbrugge", "@csallen"]

    run_agent(
        handles=handles,
        on_status=handle_status,
        on_lead=handle_lead
    )
"""

from .agent_async import run_agent, run_agent_async, AgentConfig
from .cua import NorthstarCUA

__all__ = [
    # Main entry points
    'run_agent',
    'run_agent_async',
    'AgentConfig',

    # Lower-level components (for advanced usage)
    'NorthstarCUA',
]

__version__ = '0.1.0'
