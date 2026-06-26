"""
Playwright-based browser automation tools.

Provides nine tools for browser interaction:
- navigate_tool: Navigate to a URL
- click_tool: Click an element identified by metadata
- type_tool: Type text into an input element identified by metadata
- scroll_tool: Scroll the page vertically
- wait_tool: Wait for a specified number of seconds
- go_back_tool: Navigate back to the previous page
- press_key_tool: Press a keyboard key
- get_current_url: Get the current page URL and title
- extract_elements: Extract elements matching a CSS selector

Element metadata format:
{
    "tag": "input | button | a | p | div | span | ...",
    "text": "visible text if available",
    "class": "element class names",
    "href": "link url if available",
    "placeholder": "input placeholder if available",
    "name": "input name if available",
    "role": "element role if available",
    "id": "element id if available"
}

Element selection priority (highest first):
1. id
2. role + text
3. href
4. name
5. placeholder
6. exact text
7. class
8. tag
"""

import json
import logging
import time
from typing import Dict, Any

from langchain_core.tools import tool
from playwright.sync_api import Page, Locator

from tools.browser_lifecycle import BrowserLifecycle

logger = logging.getLogger(__name__)

_browser_lifecycle: BrowserLifecycle = None

# Delay between actions so the user can visually follow along in the browser
ACTION_DELAY_SECONDS = 1.0


def set_browser_lifecycle(bl: BrowserLifecycle):
    """Set the global BrowserLifecycle instance used by all browser tools."""
    global _browser_lifecycle
    _browser_lifecycle = bl


def _get_page() -> Page:
    """Get the current page from the BrowserLifecycle instance."""
    if _browser_lifecycle is None:
        raise RuntimeError("BrowserLifecycle not initialized. Call set_browser_lifecycle() first.")
    page = _browser_lifecycle.get_page()
    if page is None:
        raise RuntimeError("Browser page is not available.")
    return page


def _find_element(page: Page, metadata: Dict[str, Any]) -> Locator:
    """Find the most relevant element matching the metadata using priority strategy.

    Tries each selection strategy in priority order and returns the first
    locator that matches at least one visible element on the page.

    Priority order (highest first):
    1. id
    2. role + text
    3. href
    4. name
    5. placeholder
    6. exact text
    7. class
    8. tag
    """
    tag = metadata.get("tag", "")
    element_id = metadata.get("id", "")
    role = metadata.get("role", "")
    text = metadata.get("text", "")
    href = metadata.get("href", "")
    name = metadata.get("name", "")
    placeholder = metadata.get("placeholder", "")
    css_class = metadata.get("class", "")

    # Build ordered list of (strategy_name, locator_factory) pairs
    strategies = []

    # 1. ID (highest priority)
    if element_id:
        strategies.append(("id", lambda: page.locator(f"#{element_id}")))

    # 2. Role + text
    if role and text:
        def _role_text():
            try:
                return page.get_by_role(role, name=text)
            except Exception:
                # Fallback if role is not a valid ARIA role
                return page.locator(f"[role='{role}']:has-text('{text}')")
        strategies.append(("role+text", _role_text))

    # 3. Href (for links)
    if href:
        strategies.append(("href", lambda: page.locator(f"a[href='{href}']")))

    # 4. Name attribute
    if name:
        strategies.append(("name", lambda: page.locator(f"[name='{name}']")))

    # 5. Placeholder
    if placeholder:
        strategies.append(("placeholder", lambda: page.locator(f"[placeholder='{placeholder}']")))

    # 6. Exact text (optionally scoped to tag)
    if text:
        def _exact_text():
            if tag:
                return page.locator(f"{tag}:has-text('{text}')")
            return page.get_by_text(text, exact=True)
        strategies.append(("text", _exact_text))

    # 7. Class (all classes combined, optionally scoped to tag)
    if css_class:
        def _class_selector():
            classes = css_class.split()
            class_part = ".".join(classes)
            if tag:
                return page.locator(f"{tag}.{class_part}")
            return page.locator(f".{class_part}")
        strategies.append(("class", _class_selector))

    # 8. Tag only (lowest priority)
    if tag:
        strategies.append(("tag", lambda: page.locator(tag)))

    # Try each strategy in priority order
    for strategy_name, strategy_fn in strategies:
        try:
            locator = strategy_fn()
            count = locator.count()
            if count > 0:
                logger.debug(f"Found element using '{strategy_name}' strategy ({count} match(es))")
                return locator.first
        except Exception as e:
            logger.debug(f"Strategy '{strategy_name}' failed: {e}")
            continue

    raise ValueError(f"No matching element found for metadata: {json.dumps(metadata)}")


@tool
def click_tool(element_metadata: Dict[str, Any]) -> str:
    """Click an element on the page identified by its metadata attributes.

    Args:
        element_metadata: Dictionary describing the element to click. Supported keys:
            - tag: HTML tag name (e.g., 'button', 'a', 'div', 'p', 'span')
            - text: visible text content of the element
            - class: CSS class names (space-separated)
            - href: link URL (for <a> tags)
            - id: element ID attribute
            - role: ARIA role (e.g., 'link', 'button')
            - name: input name attribute
            - placeholder: input placeholder text

        The element is located using this priority (highest first):
        id > role+text > href > name > placeholder > exact text > class > tag

    Returns:
        Success or error message describing the result.
    """
    try:
        page = _get_page()
        locator = _find_element(page, element_metadata)

        # Wait for element to be visible and actionable
        locator.wait_for(state="visible", timeout=10000)

        # Click the element
        locator.click(timeout=10000)

        # Wait for any navigation or DOM updates to settle
        try:
            page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass  # Page may not navigate after click

        time.sleep(ACTION_DELAY_SECONDS)
        return f"Successfully clicked element: {json.dumps(element_metadata)}"
    except Exception as e:
        return f"Error clicking element {json.dumps(element_metadata)}: {str(e)}"


@tool
def navigate_tool(url: str) -> str:
    """Navigate the browser to a new URL and wait for the page to finish loading.

    Args:
        url: The URL to navigate to.

    Returns:
        The current page URL and title after navigation completes.
    """
    try:
        page = _get_page()
        page.goto(url, wait_until="load", timeout=30000)

        current_url = page.url
        title = page.title()

        time.sleep(ACTION_DELAY_SECONDS)
        return f"Navigated to: {current_url}\nTitle: {title}"
    except Exception as e:
        return f"Error navigating to '{url}': {str(e)}"


@tool
def type_tool(element_metadata: Dict[str, Any], text: str) -> str:
    """Type text into an input element identified by its metadata attributes.

    Args:
        element_metadata: Dictionary describing the input element. Supported keys:
            - tag: HTML tag name (e.g., 'input', 'textarea')
            - text: visible text content
            - class: CSS class names (space-separated)
            - id: element ID attribute
            - role: ARIA role (e.g., 'textbox', 'input')
            - name: input name attribute
            - placeholder: input placeholder text

        The element is located using this priority (highest first):
        id > role+text > href > name > placeholder > exact text > class > tag

        text: The text to type into the element.

    Behavior:
        - Locates the target input element
        - Checks whether the input already contains text
        - If text exists, clears the field completely
        - Types the new text
        - Verifies that the text was entered successfully

    Returns:
        Success or error message describing the result.
    """
    try:
        page = _get_page()
        locator = _find_element(page, element_metadata)

        # Wait for element to be visible and actionable
        locator.wait_for(state="visible", timeout=10000)

        # Check if input already has text
        try:
            current_value = locator.input_value()
            if current_value:
                # Clear the field completely
                locator.fill("")
                logger.debug(f"Cleared existing text: '{current_value}'")
        except Exception:
            # input_value() may fail on non-input elements; proceed anyway
            pass

        # Type the new text (fill automatically clears and types)
        locator.fill(text)

        # Verify the text was entered successfully
        try:
            actual_value = locator.input_value()
            if actual_value == text:
                time.sleep(ACTION_DELAY_SECONDS)
                return f"Successfully typed '{text}' into element: {json.dumps(element_metadata)}"
            else:
                time.sleep(ACTION_DELAY_SECONDS)
                return f"Warning: Expected '{text}' but field contains '{actual_value}' in element: {json.dumps(element_metadata)}"
        except Exception:
            # Could not verify, but fill() succeeded
            time.sleep(ACTION_DELAY_SECONDS)
            return f"Typed '{text}' into element (verification skipped): {json.dumps(element_metadata)}"
    except Exception as e:
        return f"Error typing into element {json.dumps(element_metadata)}: {str(e)}"


@tool
def scroll_tool(pixels: int) -> str:
    """Scroll the page vertically by the given number of pixels. Use negative values to scroll up.
    
    Args:
        pixels: Number of pixels to scroll. Positive = down, negative = up.
    
    Returns:
        Success or error message describing the result.
    """
    try:
        page = _get_page()
        direction = "down" if pixels > 0 else "up"
        abs_pixels = abs(pixels)
        
        # Use Playwright's mouse wheel API
        page.mouse.wheel(0, pixels)
        
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Scrolled {abs_pixels}px {direction}"
    except Exception as e:
        return f"Error scrolling: {str(e)}"


@tool
def wait_tool(seconds: int) -> str:
    """Wait for a specified number of seconds for the page to load or update.
    
    Args:
        seconds: Number of seconds to wait.
    
    Returns:
        Success or error message describing the result.
    """
    try:
        page = _get_page()
        page.wait_for_timeout(seconds * 1000)
        return f"Waited {seconds} seconds"
    except Exception as e:
        return f"Error waiting: {str(e)}"


@tool
def go_back_tool(dummy: str = "") -> str:
    """Navigate back to the previous page in browser history.
    
    Args:
        dummy: Unused parameter required by some LLM tool-calling interfaces.
    
    Returns:
        The current page URL and title after going back.
    """
    try:
        page = _get_page()
        page.go_back(wait_until="load", timeout=30000)
        
        current_url = page.url
        title = page.title()
        
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Went back to: {current_url}\nTitle: {title}"
    except Exception as e:
        return f"Error going back: {str(e)}"


@tool
def press_key_tool(key: str) -> str:
    """Press a keyboard key.
    
    Args:
        key: The key to press. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown', 'ArrowUp'.
    
    Returns:
        Success or error message describing the result.
    """
    try:
        page = _get_page()
        page.keyboard.press(key)
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key '{key}': {str(e)}"


@tool
def get_current_url(dummy: str = "") -> str:
    """Get the current browser page URL and title.
    
    Args:
        dummy: Unused parameter required by some LLM tool-calling interfaces.
    
    Returns:
        The current page URL and title.
    """
    try:
        page = _get_page()
        current_url = page.url
        title = page.title()
        return f"Current URL: {current_url}\nTitle: {title}"
    except Exception as e:
        return f"Error getting current URL: {str(e)}"


@tool
def extract_elements(selector: str) -> str:
    """Extract all elements matching a CSS selector with their text and attributes.
    
    Args:
        selector: CSS selector to match elements (e.g., 'a', 'button', '.product-item', 'div.card', 'input').
    
    Returns:
        JSON string containing extracted elements with their text, href (for links), and other attributes.
        For input elements, includes placeholder, name, type, and value attributes.
    """
    try:
        page = _get_page()
        locator = page.locator(selector)
        count = locator.count()
        
        if count == 0:
            return f"No elements found matching selector: {selector}"
        
        # Limit to first 50 elements
        count = min(count, 50)
        elements = []
        
        for i in range(count):
            element = locator.nth(i)
            try:
                # Extract element data using Playwright APIs
                tag = element.evaluate("el => el.tagName.toLowerCase()")
                text = element.text_content() or ""
                text = text.strip()[:200]
                
                # Get common attributes
                href = element.get_attribute("href")
                element_id = element.get_attribute("id")
                css_class = element.get_attribute("class")
                
                # Get input-specific attributes
                placeholder = element.get_attribute("placeholder")
                name = element.get_attribute("name")
                input_type = element.get_attribute("type")
                
                # Get value for input elements (skip password fields for safety)
                value = None
                if tag in ("input", "textarea", "select"):
                    try:
                        if input_type and input_type.lower() == "password":
                            value = None  # Skip password values for safety
                        else:
                            value = element.input_value()
                    except Exception:
                        value = element.get_attribute("value")
                
                # Get aria-label for accessibility
                aria_label = element.get_attribute("aria-label")
                
                # Check visibility
                is_visible = element.is_visible()
                
                # Build element data dict
                element_data = {
                    "index": i,
                    "tag": tag,
                    "visible": is_visible
                }
                
                # Only include non-empty attributes
                if text:
                    element_data["text"] = text
                if href:
                    element_data["href"] = href
                if element_id:
                    element_data["id"] = element_id
                if css_class:
                    element_data["class"] = css_class
                if placeholder:
                    element_data["placeholder"] = placeholder
                if name:
                    element_data["name"] = name
                if input_type:
                    element_data["type"] = input_type
                if value:
                    element_data["value"] = value
                if aria_label:
                    element_data["aria_label"] = aria_label
                
                # Include elements that have any useful attribute
                # (text, href, placeholder, name, id, type, value, or aria_label)
                has_useful_attr = any([
                    text, href, placeholder, name, element_id,
                    input_type, value, aria_label
                ])
                
                if has_useful_attr:
                    elements.append(element_data)
            except Exception as e:
                logger.debug(f"Failed to extract element {i}: {e}")
                continue
        
        if not elements:
            return f"No elements with useful attributes found matching selector: {selector}"
        
        return json.dumps(elements, indent=2)
    except Exception as e:
        return f"Error extracting elements with selector '{selector}': {str(e)}"


@tool
def request_memory_search(query: str) -> str:
    """Search the memory (vector database) for relevant information from previously visited pages.
    
    Use this when you need context about page content, elements, or information
    that was extracted from pages during the browsing session.
    
    Args:
        query: A search query describing what information you're looking for.
               Example: "login form input fields", "product price information"
    
    Returns:
        JSON string containing relevant chunks from the memory database,
        or a message if no results are found.
    """
    try:
        from vector_store.faiss_db import get_vector_db
        from tools.retriever import retrieve
        
        vector_db = get_vector_db()
        results = retrieve(query, vector_db, k=15)
        
        if not results:
            return f"No relevant information found in memory for query: '{query}'"
        
        # Format results for the LLM
        formatted = []
        for i, result in enumerate(results, 1):
            text = result.get("text", "")
            metadata = result.get("metadata", {})
            formatted.append({
                "index": i,
                "text": text,
                "metadata": metadata
            })
        
        return json.dumps(formatted, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error searching memory: {str(e)}"


# List of all browser tools for easy import
ALL_BROWSER_TOOLS = [
    navigate_tool,
    click_tool,
    type_tool,
    scroll_tool,
    wait_tool,
    go_back_tool,
    press_key_tool,
    get_current_url,
    extract_elements,
    request_memory_search,
]

