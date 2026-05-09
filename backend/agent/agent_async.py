"""
Async agent orchestration for PodPipe using KERNEL browser.
This version uses KERNEL's stealth browsers for reliable Twitter access.
"""

import os
import asyncio
import base64
from typing import List, Callable, Optional, Set
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    max_profiles: int = 10
    timeout_seconds: int = 180


async def run_agent_async(
    handles: List[str],
    on_status: Callable[[str], None],
    on_lead: Callable[[dict], None],
    config: Optional[AgentConfig] = None
) -> int:
    """
    Extract profile data for a list of Twitter handles.

    This is the main entry point - Person B provides handles from LLM,
    and we verify and extract data from each profile.

    Args:
        handles: List of Twitter handles to check (from LLM suggestions)
        on_status: Status callback
        on_lead: Lead callback when profile is extracted
        config: Optional configuration

    Returns:
        Number of leads found
    """
    from kernel import Kernel
    from playwright.async_api import async_playwright
    from agent.cua import NorthstarCUA

    config = config or AgentConfig()
    leads_found = 0
    seen_handles: Set[str] = set()

    on_status("Initializing AI vision model...")
    cua = NorthstarCUA()

    kernel_api_key = os.environ.get("KERNEL_API_KEY")
    if not kernel_api_key:
        raise ValueError("KERNEL_API_KEY not set")

    on_status("Starting KERNEL cloud browser...")
    kernel = Kernel(api_key=kernel_api_key)

    # Create browser with stealth mode
    browser_session = kernel.browsers.create(
        stealth=True,
        timeout_seconds=config.timeout_seconds
    )

    on_status(f"Browser ready (session: {browser_session.session_id[:8]}...)")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(browser_session.cdp_ws_url)
            page = browser.contexts[0].pages[0]

            for handle in handles:
                if leads_found >= config.max_profiles:
                    on_status(f"Reached max {config.max_profiles} profiles")
                    break

                # Normalize handle
                handle_clean = handle.lower().lstrip('@')
                if handle_clean in seen_handles:
                    continue
                seen_handles.add(handle_clean)

                profile_url = f"https://twitter.com/{handle_clean}"
                on_status(f"Analyzing @{handle_clean}'s profile...")

                try:
                    # Navigate to profile
                    await page.goto(profile_url, timeout=20000)
                    await page.wait_for_timeout(3000)

                    # Take screenshot
                    screenshot_bytes = await page.screenshot()
                    b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    screenshot_url = f"data:image/png;base64,{b64}"

                    # Check for login wall
                    if cua.check_for_login_wall(screenshot_url):
                        on_status(f"@{handle_clean} requires login, skipping...")
                        continue

                    # Extract profile data
                    profile_data = cua.extract_profile_data(screenshot_url)

                    if not profile_data or not profile_data.get('name'):
                        on_status(f"Could not extract @{handle_clean}, skipping...")
                        continue

                    # Scroll to see tweets
                    await page.mouse.wheel(0, 400)
                    await page.wait_for_timeout(1500)

                    # Screenshot tweets
                    tweets_bytes = await page.screenshot()
                    tweets_b64 = base64.b64encode(tweets_bytes).decode('utf-8')
                    tweets_url = f"data:image/png;base64,{tweets_b64}"

                    # Extract tweets
                    tweets = cua.extract_tweets(tweets_url)

                    # Build lead data
                    lead = {
                        "name": profile_data.get('name', handle_clean),
                        "twitter_handle": f"@{handle_clean}",
                        "twitter_url": profile_url,
                        "bio": profile_data.get('bio', ''),
                        "followers": profile_data.get('followers', 0),
                        "profile_image_url": profile_data.get('profile_image_url', 'visible'),
                        "recent_tweets": tweets
                    }

                    on_lead(lead)
                    leads_found += 1
                    on_status(f"Found lead: {lead['name']} (@{handle_clean})")

                except Exception as e:
                    on_status(f"Error with @{handle_clean}: {str(e)[:50]}")
                    continue

            await browser.close()

    finally:
        # Clean up KERNEL session
        try:
            kernel.browsers.delete_by_id(browser_session.session_id)
        except:
            pass

    on_status(f"Agent completed. Found {leads_found} leads.")
    return leads_found


def run_agent(
    handles: List[str],
    on_status: Callable[[str], None],
    on_lead: Callable[[dict], None],
    config: Optional[AgentConfig] = None
) -> int:
    """
    Synchronous wrapper for run_agent_async.

    This is for compatibility - use run_agent_async directly in async code.
    """
    return asyncio.run(run_agent_async(handles, on_status, on_lead, config))
