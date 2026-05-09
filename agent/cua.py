"""
Northstar CUA (Computer Use Agent) integration.
Handles vision-based screenshot analysis and action extraction.
"""

import os
import json
import re
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class NorthstarCUA:
    """Interface to Northstar CUA model for vision-based analysis."""

    def __init__(self, api_key: Optional[str] = None):
        from tzafon import Lightcone

        self.api_key = api_key or os.environ.get("TZAFON_API_KEY")
        if not self.api_key:
            raise ValueError("TZAFON_API_KEY environment variable not set")

        self.client = Lightcone(api_key=self.api_key)
        self.model = "tzafon.northstar-cua-fast"

    def analyze_screenshot(self, screenshot_url: str, prompt: str) -> str:
        """
        Send a screenshot to Northstar and get a text response.

        Args:
            screenshot_url: URL of the screenshot image
            prompt: What to extract/analyze from the screenshot

        Returns:
            Text response from the model
        """
        # Use chat completion API for text analysis
        response = self.client.chat.create_completion(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": screenshot_url}}
                ]
            }]
        )

        # Extract text from response (returns dict)
        if isinstance(response, dict):
            choices = response.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                return message.get('content', '')

        return ""

    def extract_twitter_handles(self, screenshot_url: str) -> List[str]:
        """
        Extract Twitter handles from a search results screenshot.

        Args:
            screenshot_url: Screenshot of Twitter search results page

        Returns:
            List of Twitter handles (e.g., ["@johndoe", "@janesmith"])
        """
        prompt = """Look at this Twitter search results page.
List all the Twitter @handles (usernames) you can see for the people shown in the results.
Return ONLY the handles, one per line, starting with @.
Do not include any other text or explanation."""

        response = self.analyze_screenshot(screenshot_url, prompt)

        # Parse handles from response
        handles = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # Extract handle pattern
            match = re.search(r'@[\w]+', line)
            if match:
                handles.append(match.group())

        return handles

    def extract_twitter_handles_from_google(self, screenshot_url: str) -> List[str]:
        """
        Extract Twitter handles from Google search results.

        Args:
            screenshot_url: Screenshot of Google search results for site:twitter.com

        Returns:
            List of Twitter handles extracted from Google results
        """
        prompt = """Look at this Google search results page showing Twitter/X profiles.
Find all Twitter usernames (handles) mentioned in the search results.
Look for patterns like:
- twitter.com/username
- x.com/username
- @username

Return ONLY the handles, one per line, starting with @.
Do not include any other text or explanation.
Example output:
@johndoe
@janesmith"""

        response = self.analyze_screenshot(screenshot_url, prompt)

        # Parse handles from response
        handles = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # Extract handle pattern - either @handle or from URL
            handle_match = re.search(r'@([\w]+)', line)
            if handle_match:
                handles.append(f"@{handle_match.group(1)}")
            else:
                # Try to extract from twitter.com/handle or x.com/handle pattern
                url_match = re.search(r'(?:twitter|x)\.com/([\w]+)', line, re.IGNORECASE)
                if url_match and url_match.group(1).lower() not in ['search', 'home', 'explore', 'settings']:
                    handles.append(f"@{url_match.group(1)}")

        # Deduplicate while preserving order
        seen = set()
        unique_handles = []
        for h in handles:
            h_lower = h.lower()
            if h_lower not in seen:
                seen.add(h_lower)
                unique_handles.append(h)

        return unique_handles

    def extract_profile_data(self, screenshot_url: str) -> Dict[str, Any]:
        """
        Extract profile information from a Twitter profile screenshot.

        Args:
            screenshot_url: Screenshot of a Twitter profile page

        Returns:
            Dict with name, handle, bio, followers, profile_image_url
        """
        prompt = """Look at this Twitter profile page and extract the following information.
Return the data as JSON with these exact keys:
- name: the display name
- handle: the @username
- bio: the profile bio/description
- followers: the follower count (as a number, e.g., 12500 not "12.5K")
- profile_image_url: describe as "visible" if you can see a profile picture

Return ONLY valid JSON, no other text."""

        response = self.analyze_screenshot(screenshot_url, prompt)

        # Try to parse JSON from response
        try:
            # Clean up response - find JSON in the text
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                # Normalize followers to int
                if 'followers' in data:
                    data['followers'] = self._parse_follower_count(data['followers'])
                return data
        except json.JSONDecodeError:
            pass

        # Return empty dict if parsing fails
        return {}

    def extract_tweets(self, screenshot_url: str) -> List[str]:
        """
        Extract recent tweet texts from a screenshot of tweets.

        Args:
            screenshot_url: Screenshot showing tweets

        Returns:
            List of tweet texts (3-5 tweets)
        """
        prompt = """Look at this Twitter page showing tweets.
Extract the text content of up to 5 recent tweets visible on the page.
Return each tweet on its own line, numbered 1-5.
Only include the tweet text, not the author name or metadata.
If a tweet is cut off, include what's visible."""

        response = self.analyze_screenshot(screenshot_url, prompt)

        # Parse tweets from response
        tweets = []
        for line in response.strip().split('\n'):
            line = line.strip()
            # Remove numbering like "1.", "1)", "1:"
            cleaned = re.sub(r'^[\d]+[\.\)\:]\s*', '', line)
            if cleaned and len(cleaned) > 10:  # Filter out very short lines
                tweets.append(cleaned)

        return tweets[:5]  # Max 5 tweets

    def _parse_follower_count(self, count: Any) -> int:
        """Parse follower count from various formats."""
        if isinstance(count, int):
            return count

        if isinstance(count, str):
            # Remove commas and spaces
            count = count.replace(',', '').replace(' ', '').strip()

            # Handle K, M suffixes
            multiplier = 1
            if count.upper().endswith('K'):
                multiplier = 1000
                count = count[:-1]
            elif count.upper().endswith('M'):
                multiplier = 1000000
                count = count[:-1]

            try:
                return int(float(count) * multiplier)
            except ValueError:
                return 0

        return 0

    def check_for_login_wall(self, screenshot_url: str) -> bool:
        """
        Check if the screenshot shows a Twitter login wall.

        Args:
            screenshot_url: Screenshot to check

        Returns:
            True if login wall is detected
        """
        prompt = """Look at this screenshot. Is this showing a Twitter/X login wall,
sign-in prompt, or "Log in to continue" message?
Answer with just YES or NO."""

        response = self.analyze_screenshot(screenshot_url, prompt)
        return 'YES' in response.upper()

    def find_element_coordinates(self, screenshot_url: str, element_description: str) -> Optional[tuple]:
        """
        Find coordinates of an element in the screenshot.

        Args:
            screenshot_url: Screenshot to search
            element_description: Description of element to find

        Returns:
            (x, y) coordinates or None if not found
        """
        prompt = f"""Look at this screenshot and find: {element_description}

Return the approximate center coordinates of this element as two numbers: X Y
where X is the horizontal position (0=left edge, 1280=right edge)
and Y is the vertical position (0=top, 720=bottom).

Return ONLY two numbers separated by a space, like: 640 360"""

        response = self.analyze_screenshot(screenshot_url, prompt)

        # Parse coordinates
        match = re.search(r'(\d+)\s+(\d+)', response)
        if match:
            x, y = int(match.group(1)), int(match.group(2))
            # Validate reasonable bounds
            if 0 <= x <= 1280 and 0 <= y <= 720:
                return (x, y)

        return None
