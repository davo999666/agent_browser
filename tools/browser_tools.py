import os
import time

from langchain_core.tools import tool

from tools.browser_lifecycle import BrowserLifecycle

_browser_lifecycle: BrowserLifecycle = None

# Directory for screenshots
SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Delay between actions so the user can visually follow along in the browser
ACTION_DELAY_SECONDS = 2.0

def _highlight_element(page, selector: str, duration_ms: int = 2000):
    """Highlight an element with a colored border so the user can see what's being interacted with."""
    try:
        page.evaluate(f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (el) {{
                    el.style.outline = '4px solid red';
                    el.style.outlineOffset = '2px';
                    setTimeout(() => {{
                        el.style.outline = '';
                        el.style.outlineOffset = '';
                    }}, {duration_ms});
                }}
            }}
        """)
    except Exception:
        pass  # Don't fail if highlighting doesn't work


def set_browser_lifecycle(bl: BrowserLifecycle):
    """Set the global BrowserLifecycle instance used by all browser tools."""
    global _browser_lifecycle
    _browser_lifecycle = bl


def _get_page():
    """Get the current page from the BrowserLifecycle instance."""
    if _browser_lifecycle is None:
        raise RuntimeError("BrowserLifecycle not initialized. Call set_browser_lifecycle() first.")
    page = _browser_lifecycle.get_page()
    if page is None:
        raise RuntimeError("Browser page is not available.")
    return page


@tool
def click_tool(selector: str, index: int = 0) -> str:
    """Click an element on the page using a CSS selector or text-based locator.
    
    Args:
        selector: CSS selector or text locator (e.g., 'button.submit', '#login-btn', 'text=Sign In')
        index: If multiple elements match, click the one at this index (0-based, default: 0)
    
    Examples:
        - 'button.submit' - click submit button
        - '#login-btn' - click element with id 'login-btn'
        - 'text=Real Estate' - click element containing text 'Real Estate'
        - 'a[href="/category/54"]' - click link with specific href
    """
    try:
        page = _get_page()
        
        # Handle text-based selectors specially
        if selector.startswith('text='):
            text = selector[5:]  # Remove 'text=' prefix
            # Find all elements with this text and highlight the one we'll click
            page.evaluate(f"""
                () => {{
                    const elements = [];
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );
                    let node;
                    while (node = walker.nextNode()) {{
                        if (node.textContent.trim().includes('{text}')) {{
                            elements.push(node.parentElement);
                        }}
                    }}
                    if (elements.length > {index}) {{
                        const el = elements[{index}];
                        el.style.outline = '4px solid red';
                        el.style.outlineOffset = '2px';
                        setTimeout(() => {{
                            el.style.outline = '';
                            el.style.outlineOffset = '';
                        }}, 3000);
                    }}
                }}
            """)
            time.sleep(0.5)
            
            # Use locator with index to click specific element
            locator = page.locator(selector)
            count = locator.count()
            if count > index:
                locator.nth(index).click(timeout=10000, force=True)
            else:
                locator.first.click(timeout=10000, force=True)
        else:
            # Highlight the element before clicking so user can see it
            _highlight_element(page, selector, duration_ms=3000)
            time.sleep(0.5)  # Brief pause to see the highlight
            
            # Use locator with index for CSS selectors too
            locator = page.locator(selector)
            count = locator.count()
            if count > index:
                locator.nth(index).click(timeout=10000, force=True)
            else:
                locator.first.click(timeout=10000, force=True)
        
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Clicked element: {selector} (index={index})"
    except Exception as e:
        return f"Error clicking '{selector}': {str(e)}"


@tool
def type_tool(selector: str, text: str) -> str:
    """Type text into an input element identified by a CSS selector.
    
    Args:
        selector: CSS selector for the input element (e.g. 'input#search', '#email')
        text: The text to type into the element
    """
    try:
        page = _get_page()
        # Highlight the element before typing so user can see it
        _highlight_element(page, selector, duration_ms=3000)
        time.sleep(0.5)  # Brief pause to see the highlight
        
        # Show typing indicator
        page.evaluate(f"""
            () => {{
                const indicator = document.createElement('div');
                indicator.style.cssText = 'position:fixed;top:10px;right:10px;font-size:18px;z-index:99999;background:rgba(0,200,0,0.9);color:white;padding:15px;border-radius:10px;';
                indicator.textContent = 'Typing: "{text}"';
                document.body.appendChild(indicator);
                setTimeout(() => indicator.remove(), 2500);
            }}
        """)
        time.sleep(0.3)
        
        page.fill(selector, text)
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Typed '{text}' into {selector}"
    except Exception as e:
        return f"Error typing into '{selector}': {str(e)}"


@tool
def scroll_tool(pixels: int) -> str:
    """Scroll the page vertically by the given number of pixels. Use negative values to scroll up."""
    try:
        page = _get_page()
        # Add visual indicator showing scroll direction
        direction = "↓" if pixels > 0 else "↑"
        abs_pixels = abs(pixels)
        page.evaluate(f"""
            () => {{
                const indicator = document.createElement('div');
                indicator.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);font-size:48px;z-index:99999;background:rgba(255,0,0,0.8);color:white;padding:20px;border-radius:10px;';
                indicator.textContent = 'Scrolling {direction} {abs_pixels}px';
                document.body.appendChild(indicator);
                setTimeout(() => indicator.remove(), 1500);
            }}
        """)
        time.sleep(0.3)
        
        # Find and scroll the actual scrollable element (handles pages with overflow containers)
        scrolled = page.evaluate(f"""
            () => {{
                // Function to find the scrollable element
                function findScrollableElement() {{
                    // Check if documentElement or body is scrollable
                    const docEl = document.documentElement;
                    const body = document.body;
                    
                    // If window itself is scrollable, return null (we'll use window.scrollBy)
                    if (docEl.scrollHeight > docEl.clientHeight || body.scrollHeight > body.clientHeight) {{
                        // Check if there's a child element that's actually scrollable
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {{
                            const style = window.getComputedStyle(el);
                            const overflowY = style.overflowY;
                            const overflowX = style.overflowX;
                            if ((overflowY === 'auto' || overflowY === 'scroll' || overflowX === 'auto' || overflowX === 'scroll')
                                && el.scrollHeight > el.clientHeight) {{
                                return el;
                            }}
                        }}
                        return null; // Use window scrolling
                    }}
                    
                    // Look for scrollable containers
                    const allElements = document.querySelectorAll('*');
                    for (const el of allElements) {{
                        const style = window.getComputedStyle(el);
                        const overflowY = style.overflowY;
                        const overflowX = style.overflowX;
                        if ((overflowY === 'auto' || overflowY === 'scroll' || overflowX === 'auto' || overflowX === 'scroll')
                            && el.scrollHeight > el.clientHeight) {{
                            return el;
                        }}
                    }}
                    return null;
                }}
                
                const scrollableEl = findScrollableElement();
                if (scrollableEl) {{
                    scrollableEl.scrollBy(0, {pixels});
                    return 'element';
                }} else {{
                    window.scrollBy(0, {pixels});
                    return 'window';
                }}
            }}
        """)
        
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Scrolled {pixels}px {direction} ({scrolled})"
    except Exception as e:
        return f"Error scrolling: {str(e)}"


@tool
def navigate_tool(url: str) -> str:
    """Navigate the browser to a new URL."""
    try:
        page = _get_page()
        # Show navigation indicator
        page.evaluate(f"""
            () => {{
                const indicator = document.createElement('div');
                indicator.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);font-size:24px;z-index:99999;background:rgba(0,100,255,0.9);color:white;padding:20px;border-radius:10px;';
                indicator.textContent = 'Navigating to: {url}';
                document.body.appendChild(indicator);
                setTimeout(() => indicator.remove(), 2000);
            }}
        """)
        time.sleep(0.5)
        page.goto(url, timeout=30000)
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Navigated to {url}"
    except Exception as e:
        return f"Error navigating to '{url}': {str(e)}"


@tool
def get_page_state_tool(dummy: str = "") -> str:
    """Get the current browser page state: URL, title, visible text, links, buttons, and forms.
    Call this FIRST to observe the current page before deciding the next action.
    The dummy parameter is unused but required by some LLM tool-calling interfaces.
    """
    try:
        page = _get_page()
        current_url = page.url
        title = page.title()
        
        # Get visible text content
        text_content = page.evaluate("""
            () => {
                const body = document.body;
                if (!body) return '';
                return body.innerText.substring(0, 5000);
            }
        """)
        
        # Get all links
        links = page.evaluate("""
            () => {
                const anchors = Array.from(document.querySelectorAll('a[href]'));
                return anchors.slice(0, 30).map(a => ({
                    text: a.innerText.trim().substring(0, 50),
                    href: a.href
                })).filter(a => a.text);
            }
        """)
        
        # Get all buttons
        buttons = page.evaluate("""
            () => {
                const btns = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'));
                return btns.slice(0, 20).map(b => ({
                    text: b.innerText || b.value || '',
                    id: b.id || '',
                    class: b.className || ''
                })).filter(b => b.text);
            }
        """)
        
        # Get all forms/inputs
        forms = page.evaluate("""
            () => {
                const inputs = Array.from(document.querySelectorAll('input, select, textarea'));
                return inputs.slice(0, 20).map(i => ({
                    type: i.type || i.tagName.toLowerCase(),
                    name: i.name || '',
                    id: i.id || '',
                    placeholder: i.placeholder || ''
                }));
            }
        """)
        
        result = f"URL: {current_url}\nTitle: {title}\n\n"
        result += f"Page Content:\n{text_content}\n\n"
        
        if links:
            result += "Links:\n" + "\n".join([f"  - {l['text']}: {l['href']}" for l in links[:15]]) + "\n\n"
        
        if buttons:
            result += "Buttons:\n" + "\n".join([f"  - {b['text']} (id={b['id']}, class={b['class']})" for b in buttons[:10]]) + "\n\n"
        
        if forms:
            result += "Forms/Inputs:\n" + "\n".join([f"  - {f['type']}: name={f['name']}, id={f['id']}, placeholder={f['placeholder']}" for f in forms[:10]]) + "\n"
        
        return result
    except Exception as e:
        return f"Error getting page state: {str(e)}"


@tool
def press_key_tool(key: str) -> str:
    """Press a keyboard key. Examples: 'Enter', 'Tab', 'Escape', 'ArrowDown'."""
    try:
        page = _get_page()
        # Show key press indicator
        page.evaluate(f"""
            () => {{
                const indicator = document.createElement('div');
                indicator.style.cssText = 'position:fixed;bottom:20px;right:20px;font-size:24px;z-index:99999;background:rgba(100,0,200,0.9);color:white;padding:15px 25px;border-radius:10px;font-family:monospace;';
                indicator.textContent = '⌨️ Key: {key}';
                document.body.appendChild(indicator);
                setTimeout(() => indicator.remove(), 2000);
            }}
        """)
        time.sleep(0.3)
        page.keyboard.press(key)
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Pressed key: {key}"
    except Exception as e:
        return f"Error pressing key '{key}': {str(e)}"


@tool
def wait_tool(seconds: int) -> str:
    """Wait for a specified number of seconds for the page to load or update."""
    try:
        page = _get_page()
        page.wait_for_timeout(seconds * 1000)
        return f"Waited {seconds} seconds"
    except Exception as e:
        return f"Error waiting: {str(e)}"


@tool
def select_option_tool(selector: str, value: str) -> str:
    """Select an option in a dropdown (<select>) element.
    
    Args:
        selector: CSS selector for the <select> element (e.g. 'select#category')
        value: The value or label of the option to select
    """
    try:
        page = _get_page()
        page.select_option(selector, value)
        time.sleep(ACTION_DELAY_SECONDS)
        return f"Selected '{value}' in {selector}"
    except Exception as e:
        return f"Error selecting option in '{selector}': {str(e)}"


@tool
def get_element_info_tool(selector: str) -> str:
    """Get detailed information about a specific element: its tag, text, attributes, and visibility.
    
    Args:
        selector: CSS selector for the element to inspect
    """
    try:
        page = _get_page()
        info = page.evaluate(f"""
            () => {{
                const el = document.querySelector('{selector}');
                if (!el) return 'Element not found';
                const attrs = {{}};
                for (const attr of el.attributes) {{
                    attrs[attr.name] = attr.value;
                }}
                return JSON.stringify({{
                    tag: el.tagName.toLowerCase(),
                    text: el.innerText ? el.innerText.substring(0, 500) : '',
                    attributes: attrs,
                    visible: el.offsetParent !== null,
                    rect: el.getBoundingClientRect()
                }});
            }}
        """)
        return f"Element info for '{selector}':\n{info}"
    except Exception as e:
        return f"Error getting element info for '{selector}': {str(e)}"


@tool
def wait_for_selector_tool(selector: str) -> str:
    """Wait for an element matching the CSS selector to appear on the page (up to 10 seconds).
    
    Args:
        selector: CSS selector to wait for (e.g. '.results-loaded', '#content')
    """
    try:
        page = _get_page()
        page.wait_for_selector(selector, timeout=10000)
        return f"Element '{selector}' appeared on page"
    except Exception as e:
        return f"Timeout waiting for '{selector}': {str(e)}"


@tool
def list_clickable_elements_tool(dummy: str = "") -> str:
    """List all clickable elements on the page (links, buttons, etc.) with their selectors.
    Use this to discover what elements are available to click.
    """
    try:
        page = _get_page()
        elements = page.evaluate("""
            () => {
                const clickables = [];
                
                // Get all links
                const links = Array.from(document.querySelectorAll('a[href]'));
                links.slice(0, 30).forEach((link, idx) => {
                    const text = link.innerText.trim().substring(0, 50);
                    if (text) {
                        clickables.push({
                            type: 'link',
                            text: text,
                            selector: `a[href="${link.getAttribute('href')}"]`,
                            index: idx
                        });
                    }
                });
                
                // Get all buttons
                const buttons = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]'));
                buttons.slice(0, 20).forEach((btn, idx) => {
                    const text = (btn.innerText || btn.value || '').trim().substring(0, 50);
                    if (text) {
                        clickables.push({
                            type: 'button',
                            text: text,
                            selector: btn.id ? `#${btn.id}` : `button:nth-of-type(${idx + 1})`,
                            index: idx
                        });
                    }
                });
                
                return clickables;
            }
        """)
        
        if not elements:
            return "No clickable elements found on page"
        
        result = "Clickable Elements:\n"
        for el in elements:
            result += f"  [{el['type']}] \"{el['text']}\" → selector: '{el['selector']}' (index={el['index']})\n"
        
        return result
    except Exception as e:
        return f"Error listing clickable elements: {str(e)}"


@tool
def take_screenshot_tool(filename: str = "") -> str:
    """Take a screenshot of the current page and save it to the screenshots folder.
    Call this to visually document what you're seeing.
    
    Args:
        filename: Optional custom filename (without extension). If empty, uses timestamp.
    """
    try:
        page = _get_page()
        if not filename:
            filename = f"screenshot_{int(time.time())}"
        
        filepath = os.path.join(SCREENSHOT_DIR, f"{filename}.png")
        page.screenshot(path=filepath, full_page=False)
        return f"Screenshot saved to: {filepath}"
    except Exception as e:
        return f"Error taking screenshot: {str(e)}"


# List of all browser tools for easy import
ALL_BROWSER_TOOLS = [
    click_tool,
    type_tool,
    scroll_tool,
    navigate_tool,
    get_page_state_tool,
    press_key_tool,
    wait_tool,
    select_option_tool,
    get_element_info_tool,
    wait_for_selector_tool,
    list_clickable_elements_tool,
    take_screenshot_tool,
]