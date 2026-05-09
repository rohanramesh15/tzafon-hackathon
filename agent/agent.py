"""
Main agent orchestration for PodPipe.
Coordinates browser, CUA, and Twitter extraction to find podcast guests.
"""

import time
from typing import List, Callable, Optional, Set
from dataclasses import dataclass

from .browser import create_browser
from .cua import NorthstarCUA
from .twitter import (
    ProfileData,
    search_twitter,
    extract_profiles_from_search,
    extract_profile_data,
    scroll_and_get_more_results
)


@dataclass
class AgentConfig:
    """Configuration for the agent."""
    max_profiles_per_query: int = 5  # Max profiles to extract per search query
    max_total_profiles: int = 15  # Max total profiles across all queries
    timeout_seconds: int = 180  # 3 minute global timeout
    scroll_for_more: bool = True  # Scroll to find more results if needed


def run_agent(
    search_queries: List[str],
    on_status: Callable[[str], None],
    on_lead: Callable[[dict], None],
    config: Optional[AgentConfig] = None
) -> None:
    """
    Main agent loop that searches Twitter and extracts profile data.

    This is the entry point called by the backend API.

    Args:
        search_queries: List of Twitter search queries to execute
        on_status: Callback for status updates - on_status("Searching...")
        on_lead: Callback when a lead is found - on_lead(profile_data_dict)
        config: Optional agent configuration

    Example:
        def handle_status(msg):
            print(f"[STATUS] {msg}")

        def handle_lead(lead):
            print(f"[LEAD] Found: {lead['name']}")

        run_agent(
            search_queries=["bootstrapped SaaS founder", "indie hacker"],
            on_status=handle_status,
            on_lead=handle_lead
        )
    """
    config = config or AgentConfig()
    start_time = time.time()

    # Track seen handles for deduplication across queries
    seen_handles: Set[str] = set()
    total_leads = 0

    # Initialize CUA
    on_status("Initializing AI vision model...")
    cua = NorthstarCUA()

    # Create browser session
    with create_browser(on_status=on_status) as browser:
        for query_idx, query in enumerate(search_queries):
            # Check global timeout
            elapsed = time.time() - start_time
            if elapsed > config.timeout_seconds:
                on_status(f"Timeout reached ({config.timeout_seconds}s), stopping...")
                break

            # Check if we've hit max profiles
            if total_leads >= config.max_total_profiles:
                on_status(f"Reached maximum of {config.max_total_profiles} profiles")
                break

            on_status(f"Processing query {query_idx + 1}/{len(search_queries)}: '{query}'")

            try:
                # Search Twitter (with automatic fallback to Google if blocked)
                screenshot_url, search_method = search_twitter(
                    browser=browser,
                    query=query,
                    cua=cua,
                    on_status=on_status
                )

                # Extract handles from search results
                handles = extract_profiles_from_search(
                    screenshot_url=screenshot_url,
                    cua=cua,
                    search_method=search_method,
                    on_status=on_status
                )

                # If not enough handles and scrolling is enabled, try scrolling
                # (only for Twitter search, not Google)
                if len(handles) < config.max_profiles_per_query and config.scroll_for_more and search_method != 'google':
                    more_handles = scroll_and_get_more_results(
                        browser=browser,
                        cua=cua,
                        existing_handles=handles,
                        on_status=on_status
                    )
                    handles.extend(more_handles)

                # Process each handle
                profiles_from_query = 0
                for handle in handles:
                    # Check limits
                    if profiles_from_query >= config.max_profiles_per_query:
                        break
                    if total_leads >= config.max_total_profiles:
                        break

                    # Check timeout
                    elapsed = time.time() - start_time
                    if elapsed > config.timeout_seconds:
                        on_status("Timeout reached, stopping...")
                        break

                    # Skip if already seen
                    handle_lower = handle.lower().lstrip('@')
                    if handle_lower in seen_handles:
                        on_status(f"Skipping @{handle_lower} (already processed)")
                        continue

                    seen_handles.add(handle_lower)

                    # Extract profile data
                    profile = extract_profile_data(
                        browser=browser,
                        handle=handle,
                        cua=cua,
                        on_status=on_status
                    )

                    if profile:
                        # Send to callback
                        on_lead(profile.to_dict())
                        total_leads += 1
                        profiles_from_query += 1
                        on_status(f"Found lead: {profile.name} (@{handle_lower})")

            except Exception as e:
                on_status(f"Error processing query '{query}': {str(e)}")
                continue  # Move to next query

    on_status(f"Agent completed. Found {total_leads} leads.")


def run_agent_async(
    search_queries: List[str],
    on_status: Callable[[str], None],
    on_lead: Callable[[dict], None],
    on_done: Callable[[int], None],
    config: Optional[AgentConfig] = None
) -> None:
    """
    Wrapper that calls on_done when the agent finishes.

    Args:
        search_queries: List of Twitter search queries
        on_status: Status callback
        on_lead: Lead callback
        on_done: Called with total lead count when finished
        config: Optional configuration
    """
    total_leads = [0]  # Use list for closure

    def counting_on_lead(lead_data: dict):
        total_leads[0] += 1
        on_lead(lead_data)

    try:
        run_agent(
            search_queries=search_queries,
            on_status=on_status,
            on_lead=counting_on_lead,
            config=config
        )
    except Exception as e:
        on_status(f"Agent error: {str(e)}")
    finally:
        on_done(total_leads[0])
