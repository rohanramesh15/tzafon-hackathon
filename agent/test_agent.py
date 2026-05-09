#!/usr/bin/env python3
"""
Test script for the PodPipe agent.

Run this to verify the agent is working correctly.

Usage:
    cd agent
    pip install -r requirements.txt
    python test_agent.py
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_basic_search():
    """Test a basic Twitter search with one query."""
    from agent import run_agent, AgentConfig

    print("=" * 60)
    print("PodPipe Agent Test")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()

    # Track results
    leads = []
    statuses = []

    def on_status(msg: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        statuses.append(msg)

    def on_lead(lead: dict):
        leads.append(lead)
        print()
        print("-" * 40)
        print(f"LEAD FOUND: {lead.get('name', 'Unknown')}")
        print(f"  Handle: {lead.get('twitter_handle', 'N/A')}")
        print(f"  Followers: {lead.get('followers', 0):,}")
        print(f"  Bio: {lead.get('bio', 'N/A')[:100]}...")
        if lead.get('recent_tweets'):
            print(f"  Recent tweets: {len(lead['recent_tweets'])}")
        print("-" * 40)
        print()

    # Run with a single test query
    config = AgentConfig(
        max_profiles_per_query=3,  # Limit for testing
        max_total_profiles=5,
        timeout_seconds=120  # 2 minute timeout for test
    )

    try:
        run_agent(
            search_queries=["bootstrapped SaaS founder"],
            on_status=on_status,
            on_lead=on_lead,
            config=config
        )
    except Exception as e:
        print(f"ERROR: {e}")
        return False

    # Print summary
    print()
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(f"Total leads found: {len(leads)}")
    print(f"Status updates: {len(statuses)}")

    if leads:
        print()
        print("Leads summary:")
        for i, lead in enumerate(leads, 1):
            print(f"  {i}. {lead.get('name')} ({lead.get('twitter_handle')})")

        # Save results to file
        output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump({
                'leads': leads,
                'statuses': statuses,
                'timestamp': datetime.now().isoformat()
            }, f, indent=2)
        print(f"\nResults saved to: {output_file}")

    return len(leads) > 0


def test_cua_only():
    """Test just the CUA component with a sample image."""
    print("=" * 60)
    print("Testing CUA (Northstar) connection...")
    print("=" * 60)

    try:
        from agent.cua import NorthstarCUA
        cua = NorthstarCUA()
        print("CUA initialized successfully")
        print(f"Model: {cua.model}")
        return True
    except Exception as e:
        print(f"CUA initialization failed: {e}")
        return False


def test_browser_only():
    """Test just the browser component."""
    print("=" * 60)
    print("Testing browser connection...")
    print("=" * 60)

    try:
        from agent.browser import create_browser

        with create_browser(on_status=print) as browser:
            print("Navigating to example.com...")
            browser.navigate("https://example.com")
            browser.wait(2)

            print("Taking screenshot...")
            screenshot_url = browser.screenshot()
            print(f"Screenshot URL: {screenshot_url[:50]}...")

        print("Browser test passed")
        return True
    except Exception as e:
        print(f"Browser test failed: {e}")
        return False


def main():
    """Run all tests."""
    print()
    print("PodPipe Agent Test Suite")
    print("========================")
    print()

    # Check environment
    if not os.environ.get("TZAFON_API_KEY"):
        print("ERROR: TZAFON_API_KEY not set in environment")
        print("Make sure to create a .env file with your API key")
        sys.exit(1)

    print("Environment check passed")
    print()

    # Run tests
    results = {}

    # Test 1: CUA initialization
    results['cua'] = test_cua_only()
    print()

    # Test 2: Browser (only if CUA passed)
    if results['cua']:
        results['browser'] = test_browser_only()
        print()

    # Test 3: Full agent (only if both passed)
    if results.get('browser'):
        print("Running full agent test...")
        print("(This may take 1-2 minutes)")
        print()
        results['agent'] = test_basic_search()

    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"  {test_name}: {status}")

    all_passed = all(results.values())
    print()
    print(f"Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
