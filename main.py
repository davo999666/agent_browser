from playwright.sync_api import sync_playwright

from workflows.browser_workflow import BrowserWorkflow


def main():

    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    
    goal = "Find an apartment for sale with a budget of $50,000."
    start_url = "https://www.list.am/en/"

    agent = BrowserWorkflow()
    agent.run(goal, start_url, browser)

    browser.close()


if __name__ == "__main__":
    main()
