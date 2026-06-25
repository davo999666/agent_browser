  # change import path
import logging

from tools.browser_lifecycle import BrowserLifecycle

logging.basicConfig(level=logging.INFO)


def test_page_click():
    browser = BrowserLifecycle(
        url="https://www.list.am",
        headless=False
    )

    try:
        # start browser safely
        browser.start()
        page = browser.get_page()

        if not page:
            raise RuntimeError("Page was not created")

        # wait for page to fully stabilize
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(5000)

        # close popup safely (if exists)
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass

        page.wait_for_timeout(2000)

        # wait for login button
        page.wait_for_selector("text=Մուտք", timeout=15000)

        # click safely
        page.locator("#ma").click()

        page.wait_for_timeout(5000)

    finally:
        browser.stop()


if __name__ == "__main__":
    test_page_click()