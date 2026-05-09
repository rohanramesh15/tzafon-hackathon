"""
KERNEL cloud browser integration for PodPipe.
Uses KERNEL's stealth browser with Playwright for direct profile access.
"""

import os
import asyncio
import base64
from typing import Optional, Callable, List
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class KernelBrowserSession:
    """Wrapper for KERNEL browser session with Playwright."""
    kernel: any
    browser_session: any
    playwright: any
    browser: any
    page: any

    async def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        await self.page.goto(url, timeout=30000)

    async def wait(self, seconds: float) -> None:
        """Wait for specified seconds."""
        await self.page.wait_for_timeout(int(seconds * 1000))

    async def screenshot(self) -> bytes:
        """Take a screenshot and return bytes."""
        return await self.page.screenshot()

    async def screenshot_base64(self) -> str:
        """Take a screenshot and return as base64 data URL."""
        screenshot_bytes = await self.screenshot()
        b64 = base64.b64encode(screenshot_bytes).decode('utf-8')
        return f"data:image/png;base64,{b64}"

    async def scroll(self, dy: int = 0) -> None:
        """Scroll the page."""
        await self.page.mouse.wheel(0, dy)

    async def close(self) -> None:
        """Close browser and clean up."""
        try:
            await self.browser.close()
        except:
            pass
        try:
            self.kernel.browsers.delete_by_id(self.browser_session.session_id)
        except:
            pass


async def create_kernel_browser(
    on_status: Optional[Callable[[str], None]] = None
) -> KernelBrowserSession:
    """
    Create a KERNEL browser session with Playwright.

    Args:
        on_status: Status callback

    Returns:
        KernelBrowserSession instance
    """
    from kernel import Kernel
    from playwright.async_api import async_playwright

    api_key = os.environ.get("KERNEL_API_KEY")
    if not api_key:
        raise ValueError("KERNEL_API_KEY environment variable not set")

    if on_status:
        on_status("Starting KERNEL cloud browser with stealth mode...")

    kernel = Kernel(api_key=api_key)

    # Create browser with stealth and anti-bot features
    browser_session = kernel.browsers.create(
        stealth=True,
        timeout_seconds=180  # 3 minute timeout
    )

    if on_status:
        on_status(f"KERNEL browser started (session: {browser_session.session_id[:8]}...)")

    # Connect via Playwright
    pw = await async_playwright().start()
    browser = await pw.chromium.connect_over_cdp(browser_session.cdp_ws_url)

    # Get existing context and page
    context = browser.contexts[0]
    page = context.pages[0]

    return KernelBrowserSession(
        kernel=kernel,
        browser_session=browser_session,
        playwright=pw,
        browser=browser,
        page=page
    )


async def extract_profile_with_kernel(
    handle: str,
    cua,
    on_status: Optional[Callable[[str], None]] = None
) -> Optional[dict]:
    """
    Extract profile data using KERNEL browser.

    Args:
        handle: Twitter handle (with or without @)
        cua: NorthstarCUA instance
        on_status: Status callback

    Returns:
        Profile data dict or None
    """
    handle = handle.lstrip('@')
    profile_url = f"https://twitter.com/{handle}"

    if on_status:
        on_status(f"Analyzing @{handle}'s profile with KERNEL...")

    session = None
    try:
        session = await create_kernel_browser(on_status)

        # Navigate to profile
        await session.navigate(profile_url)
        await session.wait(3)

        # Take screenshot
        screenshot_b64 = await session.screenshot_base64()

        # Check for login wall
        if cua.check_for_login_wall(screenshot_b64):
            if on_status:
                on_status(f"@{handle}'s profile requires login, skipping...")
            return None

        # Extract profile data
        profile_data = cua.extract_profile_data(screenshot_b64)

        if not profile_data or not profile_data.get('name'):
            if on_status:
                on_status(f"Could not extract data for @{handle}, skipping...")
            return None

        # Scroll to see tweets
        await session.scroll(dy=400)
        await session.wait(1.5)

        # Screenshot tweets
        tweets_screenshot = await session.screenshot_base64()
        tweets = cua.extract_tweets(tweets_screenshot)

        return {
            "name": profile_data.get('name', handle),
            "twitter_handle": f"@{handle}",
            "twitter_url": profile_url,
            "bio": profile_data.get('bio', ''),
            "followers": profile_data.get('followers', 0),
            "profile_image_url": profile_data.get('profile_image_url', ''),
            "recent_tweets": tweets
        }

    except Exception as e:
        if on_status:
            on_status(f"Error extracting @{handle}: {str(e)}")
        return None

    finally:
        if session:
            await session.close()


async def verify_handles_with_kernel(
    handles: List[str],
    cua,
    on_status: Optional[Callable[[str], None]] = None,
    on_lead: Optional[Callable[[dict], None]] = None,
    max_profiles: int = 10
) -> List[dict]:
    """
    Verify a list of handles by visiting their profiles.

    Args:
        handles: List of Twitter handles to verify
        cua: NorthstarCUA instance
        on_status: Status callback
        on_lead: Lead callback
        max_profiles: Maximum profiles to extract

    Returns:
        List of verified profile data
    """
    profiles = []
    seen = set()

    for handle in handles[:max_profiles * 2]:  # Check more than max in case some fail
        if len(profiles) >= max_profiles:
            break

        handle_lower = handle.lower().lstrip('@')
        if handle_lower in seen:
            continue
        seen.add(handle_lower)

        profile = await extract_profile_with_kernel(handle, cua, on_status)

        if profile:
            profiles.append(profile)
            if on_lead:
                on_lead(profile)

    return profiles
