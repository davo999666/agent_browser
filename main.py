from tools.browser_lifecycle import BrowserLifecycle
from tools.browser_tools import set_browser_lifecycle
from workflows.browser_workflow import BrowserWorkflow


def main():
    goal = "Find an apartment for sale with a price $50,000."
    start_url = "https://www.list.am/en/"

    browser_lifecycle = BrowserLifecycle(url=start_url, headless=False)

    try:
        browser_lifecycle.start()
        set_browser_lifecycle(browser_lifecycle)

        agent = BrowserWorkflow()
        agent.run(goal, start_url)
    finally:
        browser_lifecycle.stop()


if __name__ == "__main__":
    main()
