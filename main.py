from tools.browser_lifecycle import BrowserLifecycle
from workflows.browser_workflow import BrowserWorkflow


def main():
    goal = "Find an apartment for sale with a budget of $50,000."
    start_url = "https://www.list.am/en/"

    browser_lifecycle = BrowserLifecycle(url=start_url, headless=False)

    try:
        browser_lifecycle.start()

        agent = BrowserWorkflow()
        agent.run(goal, start_url, browser_lifecycle)
    finally:
        browser_lifecycle.stop()


if __name__ == "__main__":
    main()
