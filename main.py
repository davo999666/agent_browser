from workflows.browser_workflow import BrowserWorkflow


def main():
    goal = "Find an apartment for sale with a budget of $50,000."
    start_url = "https://list.am"

    agent = BrowserWorkflow()
    agent.run(goal, start_url)


if __name__ == "__main__":
    main()
