from wordle_assist import (
    WordleEngine,
    load_dictionary,
    load_illegal_combos,
)

def main():

    print("=== Smart Wordle Helper ===")

    illegal_combos = load_illegal_combos(
        "illegalcombos.txt"
    )

    while True:

        try:
            word_length = int(
                input("\nEnter word length: ")
            )
        except ValueError:
            print("Invalid number.")
            continue

        use_dictionary = (
            input("Use dictionary? (y/n): ")
            .strip()
            .lower()
            == "y"
        )

        dictionary = None

        if use_dictionary:

            try:
                dictionary = load_dictionary(
                    "words.txt",
                    word_length
                )
            except FileNotFoundError as error:
                print(error)
                continue

        engine = WordleEngine(
            word_length=word_length,
            dictionary=dictionary,
            illegal_combos=illegal_combos,
        )

        while True:

            try:
                possible_words = engine.get_possible_words()

                print(
                    f"\nPossible words remaining: "
                    f"{len(possible_words)}"
                )

                if len(possible_words) <= 100:
                    print(possible_words)

            except RuntimeError as error:
                print(error)

            command = input(
                "\nEnter guess "
                "(or manual/reset/force/exit): "
            ).strip().lower()

            if command == "exit":
                return

            if command == "reset":
                break

            if command == "force":

                try:
                    possible_words = (
                        engine.get_possible_words(force=True)
                    )

                    print(
                        f"Generated {len(possible_words)} words."
                    )

                except Exception as error:
                    print(error)

                continue

            if command == "manual":
                # CLI-specific manual input handling here
                continue

            guess = command

            if len(guess) != word_length:
                print("Guess length mismatch.")
                continue

            result = input(
                "Enter result (g/y/b): "
            ).strip().lower()

            try:
                engine.apply_feedback(
                    guess,
                    result
                )
            except ValueError as error:
                print(error)
                continue


if __name__ == "__main__":
    main()