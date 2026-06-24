from typing import Dict, Any



# keep playwright globally inside workflow
# p = sync_playwright().start()
# browser = p.chromium.launch(headless=False)


def browser_node(state: Dict[str, Any]) -> Dict[str, Any]:
    url = state["start_url"]
    browser = state["browser"]

    page = browser.new_page()

    page.goto(url, timeout=60000)
    page.wait_for_selector("a[href]", timeout=60000)

    title = page.title()
    current_url = page.url

    page_data = page.evaluate("""
() => {
    // Tags we never want to look at or descend into
    const SKIP_TAGS = new Set([
        'SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK',
        'HEAD', 'TEMPLATE', 'SVG', 'PATH', 'IFRAME', 'OBJECT', 'EMBED'
    ]);

    // Tags that are considered "meaningful" element types worth capturing
    const MEANINGFUL_TAGS = new Set([
        'A', 'BUTTON', 'INPUT', 'TEXTAREA', 'SELECT', 'OPTION', 'LABEL',
        'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
        'P', 'SPAN', 'LI', 'TD', 'TH', 'IMG', 'FIGCAPTION',
        'SUMMARY', 'DIV', 'SECTION', 'ARTICLE', 'NAV', 'FORM'
    ]);

    const results = [];
    const seenTexts = new Set(); // crude dedupe for repeated identical text nodes

    function normalize(str) {
        if (!str) return '';
        return str.replace(/\\s+/g, ' ').trim();
    }

    // Infer a role even if no explicit role attribute exists
    function inferRole(el) {
        const explicitRole = el.getAttribute('role');
        if (explicitRole) return explicitRole;

        const tag = el.tagName;
        switch (tag) {
            case 'A':
                return el.hasAttribute('href') ? 'link' : 'text';
            case 'BUTTON':
                return 'button';
            case 'INPUT': {
                const type = (el.getAttribute('type') || 'text').toLowerCase();
                if (type === 'submit' || type === 'button') return 'button';
                if (type === 'checkbox') return 'checkbox';
                if (type === 'radio') return 'radio';
                return 'input';
            }
            case 'TEXTAREA':
                return 'input';
            case 'SELECT':
                return 'combobox';
            case 'OPTION':
                return 'option';
            case 'LABEL':
                return 'label';
            case 'IMG':
                return 'image';
            case 'H1': case 'H2': case 'H3':
            case 'H4': case 'H5': case 'H6':
                return 'heading';
            case 'NAV':
                return 'navigation';
            case 'FORM':
                return 'form';
            case 'LI':
                return 'listitem';
            case 'SUMMARY':
                return 'summary';
            default:
                return null;
        }
    }

    // Pull only the element's own direct text (not nested children's text),
    // to avoid massive duplicate blobs from container divs.
    function getOwnText(el) {
        let text = '';
        for (const node of el.childNodes) {
            if (node.nodeType === Node.TEXT_NODE) {
                text += node.textContent;
            }
        }
        return normalize(text);
    }

    function isVisible(el) {
        if (!(el instanceof Element)) return false;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
            return false;
        }
        const rect = el.getBoundingClientRect();
        if (rect.width === 0 && rect.height === 0) return false;
        return true;
    }

    function buildItem(el) {
        const tag = el.tagName;
        const item = {};

        item.tag = tag.toLowerCase();

        const className = (el.getAttribute('class') || '').trim();
        if (className) item.class = className;

        // Text: own text first; for headings/buttons/links/labels fall back to full innerText
        let text = getOwnText(el);
        if (!text && ['A', 'BUTTON', 'LABEL', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'SUMMARY', 'OPTION'].includes(tag)) {
            text = normalize(el.innerText || el.textContent);
        }
        if (text) item.text = text;

        const href = el.getAttribute('href');
        if (href) item.href = href;

        const title = el.getAttribute('title');
        if (title) item.title = normalize(title);

        const placeholder = el.getAttribute('placeholder');
        if (placeholder) item.placeholder = normalize(placeholder);

        // value for inputs (skip passwords for safety)
        if (tag === 'INPUT') {
            const type = (el.getAttribute('type') || 'text').toLowerCase();
            if (type !== 'password') {
                const value = el.value || el.getAttribute('value');
                if (value) item.value = normalize(value);
            }
            const name = el.getAttribute('name');
            if (name) item.name = name;
        }

        // alt text for images
        if (tag === 'IMG') {
            const alt = el.getAttribute('alt');
            if (alt) item.text = normalize(alt);
            const src = el.getAttribute('src');
            if (src) item.src = src;
        }

        // aria-label as a fallback for accessible naming
        const ariaLabel = el.getAttribute('aria-label');
        if (ariaLabel && !item.text) item.text = normalize(ariaLabel);

        const role = inferRole(el);
        if (role) item.role = role;

        const id = el.getAttribute('id');
        if (id) item.id = id;

        return item;
    }

    // Decide if a built item has enough substance to keep
    function isUseful(item) {
        return Boolean(
            item.text || item.href || item.placeholder ||
            item.title || item.value || item.src
        );
    }

    function traverse(node) {
        if (!node || node.nodeType !== Node.ELEMENT_NODE) return;
        const el = node;
        const tag = el.tagName;

        if (SKIP_TAGS.has(tag)) return; // skip entirely, don't descend
        if (el.hasAttribute('hidden')) return;
        if (el.getAttribute('aria-hidden') === 'true') return;

        let visible = true;
        try {
            visible = isVisible(el);
        } catch (e) {
            visible = true;
        }

        if (visible && MEANINGFUL_TAGS.has(tag)) {
            const item = buildItem(el);
            if (isUseful(item)) {
                // Dedupe identical (tag+text+href) combos that often repeat in lists/menus
                const key = `${item.tag}|${item.text || ''}|${item.href || ''}|${item.placeholder || ''}`;
                if (!seenTexts.has(key)) {
                    seenTexts.add(key);
                    results.push(item);
                }
            }
        }

        // Recurse into children regardless (a DIV might not be "useful" itself
        // but its children could be)
        for (const child of el.children) {
            traverse(child);
        }
    }

    traverse(document.body);

    return results;
}
""")

    return {
        "page": page,
        "url": current_url,
        "page_content": {
                            "title": title,
                            "data": page_data
                        }
    }


