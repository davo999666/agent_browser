import json
import time
from typing import Dict, Any
from tools.browser_tools import _get_page


def browser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("=========browser_node==========")

    page = _get_page()
    if page is None:
        raise RuntimeError("BrowserLifecycle page is not available.")

    # Wait for full page load to avoid context destruction during navigation
    page.wait_for_load_state("load")
    # Additional small delay to let dynamic content settle
    time.sleep(0.5)

    title = page.title()
    current_url = page.url

    elements = page.locator("""
    a,
    button,
    input,
    textarea,
    select,
    option,
    label,
    h1,h2,h3,h4,h5,h6,
    p,
    span,
    li,
    td,
    th,
    img,
    figcaption,
    summary,
    div,
    section,
    article,
    nav,
    form
    """)

    # Retry evaluate_all to handle transient navigation errors
    max_retries = 3
    page_data = None
    for attempt in range(max_retries):
        try:
            page_data = elements.evaluate_all("""
            elements => elements.map(el => {
                const item = {
                    tag: el.tagName.toLowerCase()
                };

                const text = (el.innerText || el.textContent || "").trim();
                if (text) item.text = text;

                const href = el.getAttribute("href");
                if (href) item.href = href;

                const src = el.getAttribute("src");
                if (src) item.src = src;

                if (el.id) item.id = el.id;

                if (el.className) item.class = el.className;

                const role = el.getAttribute("role");
                if (role) item.role = role;

                const title = el.getAttribute("title");
                if (title) item.title = title;

                const placeholder = el.getAttribute("placeholder");
                if (placeholder) item.placeholder = placeholder;

                if ("value" in el && el.value) item.value = el.value;

                const type = el.getAttribute("type");
                if (type) item.type = type;

                const name = el.getAttribute("name");
                if (name) item.name = name;

                if (el.hasAttribute("checked")) item.checked = true;
                if (el.hasAttribute("disabled")) item.disabled = true;

                return item;
            })
            """)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"  ⚠️ evaluate_all failed (attempt {attempt + 1}), retrying...")
                page.wait_for_load_state("load")
                time.sleep(1)
            else:
                raise RuntimeError(f"Failed to evaluate page elements after {max_retries} attempts: {e}")

    # ---------------- OUTPUT JSON ----------------
    with open("output/page_data.json", "w", encoding="utf-8") as f:
        json.dump(page_data, f, indent=2, ensure_ascii=False)
    
    
    
    return {
        "page": page,
        "url": current_url,
        "page_content": {
            "title": title,
            "data": page_data
        }
    }