import json


def worker_node(state):
    print("\n🔥 WORKER STARTED")

    browser = state.get("browser")
    if not browser:
        print("❌ NO BROWSER IN STATE")
        return state

    # get page safely
    context = browser.contexts[0]
    page = context.pages[0] if context.pages else context.new_page()

    print("🌐 URL:", page.url)

    # ---------------- PLAN ----------------
    plan_raw = state.get("plan")
    print("📦 RAW PLAN:", plan_raw)

    if isinstance(plan_raw, str):
        try:
            plan = json.loads(plan_raw)
        except Exception as e:
            print("❌ PLAN JSON ERROR:", e)
            return state
    else:
        plan = plan_raw or {}

    steps = plan.get("steps", [])
    print(f"📌 STEPS COUNT: {len(steps)}")

    results = []

    # ---------------- EXECUTION ----------------
    for i, step in enumerate(steps):
        print(f"\n➡️ STEP {i+1}: {step}")

        action = step.get("action")
        element = step.get("element")
        input_text = step.get("input")

        try:

            # ---------------- CLICK ----------------
            if action == "click":
                print(f"🖱 CLICK -> {element}")

                try:
                    # best: partial text match
                    page.locator("a,button,div,span").filter(
                        has_text=element
                    ).first.click(timeout=5000)

                except Exception as e1:
                    print("⚠ TEXT CLICK FAILED:", e1)

                    try:
                        # fallback: raw text
                        page.get_by_text(element, exact=False).first.click(timeout=5000)

                    except Exception as e2:
                        print("❌ CLICK FAILED:", e2)

            # ---------------- TYPE ----------------
            elif action == "type":
                print(f"⌨ TYPE -> {element} = {input_text}")

                try:
                    locator = page.get_by_placeholder(element)
                    locator.fill(input_text or "")

                except:
                    try:
                        locator = page.locator("input, textarea").first
                        locator.fill(input_text or "")
                    except Exception as e:
                        print("❌ TYPE FAILED:", e)

            # ---------------- SEARCH ----------------
            elif action == "search":
                print(f"🔎 SEARCH -> {element}")

                try:
                    locator = page.locator("input, textarea").first
                    locator.fill(input_text or "")
                    locator.press("Enter")
                except Exception as e:
                    print("❌ SEARCH FAILED:", e)

            # ---------------- NAVIGATE ----------------
            elif action == "navigate":
                print(f"🌐 NAVIGATE -> {element}")
                try:
                    page.goto(element, timeout=60000)
                except Exception as e:
                    print("❌ NAVIGATE FAILED:", e)

            # ---------------- SELECT ----------------
            elif action == "select":
                print(f"📌 SELECT -> {element}")
                try:
                    page.select_option(element, input_text)
                except Exception as e:
                    print("❌ SELECT FAILED:", e)

            else:
                print("⚠ UNKNOWN ACTION:", action)

            results.append({
                "step_id": step.get("id"),
                "status": "done"
            })

        except Exception as e:
            print("❌ STEP ERROR:", str(e))

            results.append({
                "step_id": step.get("id"),
                "status": "failed",
                "error": str(e)
            })

    print("\n🔥 WORKER FINISHED\n")

    return {
        **state,
        "execution_results": results
    }