from app.agent import MealCalorieAgent


def print_trace(
    trace: list[dict],
) -> None:

    print("\nAGENT TRACE")
    print("=" * 72)

    for item in trace:
        print(item)

    print("=" * 72)


def main() -> None:

    print(
        "Meal Calorie Helper — Groq AI Agent"
    )

    print(
        "Type 'quit' to exit."
    )

    try:

        agent = MealCalorieAgent()

    except Exception as exc:

        raise SystemExit(
            f"Startup error: {exc}"
        ) from exc


    while True:

        try:

            user_text = input(
                "\nYou: "
            ).strip()

        except (
            KeyboardInterrupt,
            EOFError,
        ):

            print(
                "\nExiting."
            )

            break


        if user_text.lower() in {
            "quit",
            "exit",
        }:

            break


        if not user_text:

            continue


        try:

            result = agent.run(
                user_text
            )

            print(
                f"\nAgent: {result['answer']}"
            )

            print_trace(
                result["trace"]
            )

        except Exception as exc:

            print(
                f"\nAgent error: {exc}"
            )


if __name__ == "__main__":
    main()