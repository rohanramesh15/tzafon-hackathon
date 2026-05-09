"""
Browser management for PodPipe agent.
Handles cloud browser creation and basic operations using Lightcone SDK.
"""

import os
from typing import Optional, Callable
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BrowserSession:
    """Wrapper for a cloud browser session (ComputerSession)."""

    def __init__(self, computer):
        self.computer = computer
        self._screenshot_url: Optional[str] = None

    def navigate(self, url: str) -> None:
        """Navigate to a URL."""
        self.computer.navigate(url)

    def screenshot(self) -> str:
        """Take a screenshot and return the URL."""
        result = self.computer.screenshot()
        self._screenshot_url = self.computer.get_screenshot_url(result)
        return self._screenshot_url

    def click(self, x: int, y: int) -> None:
        """Click at coordinates."""
        self.computer.click(x, y)

    def type_text(self, text: str) -> None:
        """Type text."""
        self.computer.type(text)

    def hotkey(self, key: str) -> None:
        """Press a key or key combination."""
        self.computer.hotkey(key)

    def scroll(self, dx: int = 0, dy: int = 0) -> None:
        """Scroll the page."""
        self.computer.scroll(dx=dx, dy=dy)

    def wait(self, seconds: float) -> None:
        """Wait for specified seconds."""
        self.computer.wait(seconds)


class BrowserContextManager:
    """Context manager for browser sessions using Lightcone SDK."""

    def __init__(self, on_status: Optional[Callable[[str], None]] = None):
        self.on_status = on_status
        self._computer = None
        self._client = None
        self._context = None

    def __enter__(self) -> BrowserSession:
        from tzafon import Lightcone

        api_key = os.environ.get("TZAFON_API_KEY")
        if not api_key:
            raise ValueError("TZAFON_API_KEY environment variable not set")

        if self.on_status:
            self.on_status("Starting cloud browser...")

        self._client = Lightcone(api_key=api_key)

        # Create browser session - returns a context manager
        self._context = self._client.computer.create(kind="browser")
        self._computer = self._context.__enter__()

        if self.on_status:
            self.on_status("Cloud browser started successfully")

        return BrowserSession(computer=self._computer)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._context:
            try:
                self._context.__exit__(exc_type, exc_val, exc_tb)
            except Exception:
                pass  # Ignore cleanup errors
        return False


def create_browser(on_status: Optional[Callable[[str], None]] = None) -> BrowserContextManager:
    """
    Create a browser context manager.

    Usage:
        with create_browser(on_status=print) as browser:
            browser.navigate("https://twitter.com")
            screenshot_url = browser.screenshot()

    Args:
        on_status: Optional callback for status updates

    Returns:
        BrowserContextManager that yields a BrowserSession
    """
    return BrowserContextManager(on_status=on_status)
