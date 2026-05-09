"""
Twitter browsing and data extraction.
Uses cloud browser + Northstar CUA for vision-based scraping.
"""

import urllib.parse
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

from .cua import NorthstarCUA


@dataclass
class ProfileData:
    """Structured Twitter profile data."""
    name: str
    twitter_handle: str
    twitter_url: str
    bio: str
    followers: int
    profile_image_url: str
    recent_tweets: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_search_url(query: str, tab: str = "user") -> str:
    """
    Build a Twitter search URL.

    Args:
        query: Search query text
        tab: Search tab - "user" for People, "live" for Latest, etc.

    Returns:
        Full Twitter search URL
    """
    encoded_query = urllib.parse.quote(query)
    return f"https://twitter.com/search?q={encoded_query}&src=typed_query&f={tab}"


def build_mobile_search_url(query: str) -> str:
    """Build mobile Twitter search URL (fallback for login walls)."""
    encoded_query = urllib.parse.quote(query)
    return f"https://mobile.twitter.com/search?q={encoded_query}&src=typed_query&f=user"


def build_google_search_url(query: str) -> str:
    """Build Google search URL for Twitter profiles (fallback when Twitter blocks)."""
    # Search Google for Twitter profiles matching the query
    search_query = f"site:twitter.com {query}"
    encoded_query = urllib.parse.quote(search_query)
    return f"https://www.google.com/search?q={encoded_query}"


def build_duckduckgo_search_url(query: str) -> str:
    """Build DuckDuckGo search URL for Twitter profiles (more automation-friendly)."""
    search_query = f"site:twitter.com {query}"
    encoded_query = urllib.parse.quote(search_query)
    return f"https://duckduckgo.com/?q={encoded_query}"


def check_twitter_error(cua: NorthstarCUA, screenshot_url: str) -> bool:
    """Check if the screenshot shows a Twitter error page."""
    response = cua.analyze_screenshot(
        screenshot_url,
        "Does this page show an error message like 'Something went wrong' or 'Try reloading'? Answer YES or NO only."
    )
    return 'YES' in response.upper()


def search_twitter(
    browser,
    query: str,
    cua: NorthstarCUA,
    on_status: Optional[Callable[[str], None]] = None,
    use_mobile: bool = False,
    use_google: bool = False
) -> tuple:
    """
    Navigate to Twitter search and return screenshot URL.

    Args:
        browser: BrowserSession instance
        query: Search query
        cua: NorthstarCUA instance for analysis
        on_status: Status callback
        use_mobile: Use mobile Twitter (fallback)
        use_google: Use Google search (fallback when Twitter blocks)

    Returns:
        Tuple of (screenshot_url, search_method) where search_method is 'twitter', 'mobile', or 'google'
    """
    if use_google:
        url = build_google_search_url(query)
        search_method = 'google'
        if on_status:
            on_status(f"Searching Google for Twitter profiles: '{query}'...")
    elif use_mobile:
        url = build_mobile_search_url(query)
        search_method = 'mobile'
        if on_status:
            on_status(f"Searching mobile Twitter for '{query}'...")
    else:
        url = build_search_url(query)
        search_method = 'twitter'
        if on_status:
            on_status(f"Searching Twitter for '{query}'...")

    browser.navigate(url)
    browser.wait(4)  # Wait for page load

    screenshot_url = browser.screenshot()

    # Check for login wall
    if cua.check_for_login_wall(screenshot_url):
        if not use_mobile and not use_google:
            if on_status:
                on_status("Login wall detected, trying mobile Twitter...")
            return search_twitter(browser, query, cua, on_status, use_mobile=True)
        elif use_mobile and not use_google:
            if on_status:
                on_status("Mobile login wall detected, trying Google search...")
            return search_twitter(browser, query, cua, on_status, use_google=True)
        else:
            raise Exception("All search methods failed - login required")

    # Check for Twitter error page
    if search_method in ('twitter', 'mobile') and check_twitter_error(cua, screenshot_url):
        if not use_google:
            if on_status:
                on_status("Twitter error detected, falling back to Google search...")
            return search_twitter(browser, query, cua, on_status, use_google=True)

    return screenshot_url, search_method


def extract_profiles_from_search(
    screenshot_url: str,
    cua: NorthstarCUA,
    search_method: str = 'twitter',
    on_status: Optional[Callable[[str], None]] = None
) -> List[str]:
    """
    Extract Twitter handles from a search results screenshot.

    Args:
        screenshot_url: Screenshot of search results
        cua: NorthstarCUA instance
        search_method: 'twitter', 'mobile', or 'google'
        on_status: Status callback

    Returns:
        List of Twitter handles (5-10 handles)
    """
    if on_status:
        on_status("Extracting profiles from search results...")

    if search_method == 'google':
        handles = cua.extract_twitter_handles_from_google(screenshot_url)
    else:
        handles = cua.extract_twitter_handles(screenshot_url)

    if on_status:
        on_status(f"Found {len(handles)} profiles")

    # Return up to 10 handles
    return handles[:10]


def extract_profile_data(
    browser,
    handle: str,
    cua: NorthstarCUA,
    on_status: Optional[Callable[[str], None]] = None
) -> Optional[ProfileData]:
    """
    Extract full profile data for a Twitter user.

    Args:
        browser: BrowserSession instance
        handle: Twitter handle (with or without @)
        cua: NorthstarCUA instance
        on_status: Status callback

    Returns:
        ProfileData or None if extraction fails
    """
    # Normalize handle
    handle = handle.lstrip('@')
    profile_url = f"https://twitter.com/{handle}"

    if on_status:
        on_status(f"Analyzing @{handle}'s profile...")

    try:
        # Navigate to profile
        browser.navigate(profile_url)
        browser.wait(2)

        # Screenshot profile header
        profile_screenshot = browser.screenshot()

        # Check for login wall or private profile
        if cua.check_for_login_wall(profile_screenshot):
            if on_status:
                on_status(f"@{handle}'s profile requires login, skipping...")
            return None

        # Extract profile data
        profile_data = cua.extract_profile_data(profile_screenshot)

        if not profile_data:
            if on_status:
                on_status(f"Could not extract data for @{handle}, skipping...")
            return None

        # Scroll down to see tweets
        browser.scroll(dy=400)
        browser.wait(1)

        # Screenshot tweets section
        tweets_screenshot = browser.screenshot()

        # Extract tweets
        tweets = cua.extract_tweets(tweets_screenshot)

        # Build ProfileData
        return ProfileData(
            name=profile_data.get('name', handle),
            twitter_handle=f"@{handle}",
            twitter_url=profile_url,
            bio=profile_data.get('bio', ''),
            followers=profile_data.get('followers', 0),
            profile_image_url=profile_data.get('profile_image_url', ''),
            recent_tweets=tweets
        )

    except Exception as e:
        if on_status:
            on_status(f"Error extracting @{handle}: {str(e)}")
        return None


def scroll_and_get_more_results(
    browser,
    cua: NorthstarCUA,
    existing_handles: List[str],
    on_status: Optional[Callable[[str], None]] = None
) -> List[str]:
    """
    Scroll down search results and extract more handles.

    Args:
        browser: BrowserSession instance
        cua: NorthstarCUA instance
        existing_handles: Already extracted handles (for deduplication)
        on_status: Status callback

    Returns:
        List of new handles found
    """
    if on_status:
        on_status("Scrolling for more results...")

    browser.scroll(dy=500)
    browser.wait(2)

    screenshot_url = browser.screenshot()
    new_handles = cua.extract_twitter_handles(screenshot_url)

    # Deduplicate
    existing_set = set(h.lower() for h in existing_handles)
    unique_new = [h for h in new_handles if h.lower() not in existing_set]

    if on_status and unique_new:
        on_status(f"Found {len(unique_new)} more profiles")

    return unique_new
