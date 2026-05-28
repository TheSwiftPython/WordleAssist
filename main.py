from collections import Counter, defaultdict
import itertools
import string
import os
import re

# =========================================================
# CONFIG
# =========================================================

DICTIONARY_FILE = "words.txt"
ILLEGAL_COMBOS_FILE = "illegalcombos.txt"
OUTPUT_FILE = "output.txt"

# Maximum combinations allowed before refusing generation
MAX_GENERATION_SIZE = 500_000

# =========================================================
# CONSTRAINT CLASS
# =========================================================

class WordConstraints:

    def __init__(self, word_length):

        self.word_length = word_length

        self.excluded = set()

        self.required = defaultdict(int)

        self.known_positions = {}

        self.forbidden_positions = defaultdict(set)

    def update_from_feedback(self, guess, result):

        guess = guess.lower()
        result = result.lower()

        local_required = Counter()

        # Greens and yellows
        for i, (letter, status) in enumerate(zip(guess, result)):

            if status == "g":

                self.known_positions[i] = letter
                local_required[letter] += 1

            elif status == "y":

                self.forbidden_positions[i].add(letter)
                local_required[letter] += 1

        # Required counts
        for letter, count in local_required.items():

            self.required[letter] = max(
                self.required[letter],
                count
            )

        # Blacks
        for i, (letter, status) in enumerate(zip(guess, result)):

            if status == "b":

                if letter in self.required:
                    self.forbidden_positions[i].add(letter)
                else:
                    self.excluded.add(letter)

    def display(self):

        print("\n=== Current Constraints ===")

        print(f"Excluded Letters: {sorted(self.excluded)}")
        print(f"Required Letters: {dict(self.required)}")
        print(f"Known Positions: {self.known_positions}")

        print("Forbidden Positions:")

        for pos, letters in self.forbidden_positions.items():
            print(f"  Position {pos}: {sorted(letters)}")

# =========================================================
# FILE LOADERS
# =========================================================

def load_dictionary(word_length):

    if not os.path.exists(DICTIONARY_FILE):

        print(f"[!] Dictionary file '{DICTIONARY_FILE}' not found.")
        return []

    words = []

    with open(DICTIONARY_FILE, "r", encoding="utf-8") as f:

        for line in f:

            word = line.strip().lower()

            if len(word) == word_length and word.isalpha():
                words.append(word)

    print(f"Loaded {len(words)} dictionary words.")

    return words


def load_illegal_combos():

    if not os.path.exists(ILLEGAL_COMBOS_FILE):
        return set()

    combos = set()

    with open(ILLEGAL_COMBOS_FILE, "r", encoding="utf-8") as f:

        for line in f:

            pair = line.strip().lower()

            if len(pair) == 2:
                combos.add(pair)

    print(f"Loaded {len(combos)} illegal combinations.")

    return combos

# =========================================================
# LEGAL POSITION GENERATION
# =========================================================

def build_legal_positions(word_length, constraints):

    alphabet = set(string.ascii_lowercase)

    legal_positions = []

    for pos in range(word_length):

        legal = alphabet.copy()

        # Remove excluded letters
        legal -= constraints.excluded

        # Known positions override everything
        if pos in constraints.known_positions:
            legal = {constraints.known_positions[pos]}

        # Remove forbidden letters
        if pos in constraints.forbidden_positions:
            legal -= constraints.forbidden_positions[pos]

        legal_positions.append(sorted(legal))

    return legal_positions


def estimate_search_space(legal_positions):

    total = 1

    for letters in legal_positions:
        total *= len(letters)

    return total


def generate_possible_words(legal_positions):

    return (
        ''.join(combo)
        for combo in itertools.product(*legal_positions)
    )

# =========================================================
# FILTERING
# =========================================================

def build_regex(constraints):

    pattern = []

    for i in range(constraints.word_length):

        if i in constraints.known_positions:
            pattern.append(constraints.known_positions[i])
        else:
            pattern.append(".")

    return re.compile("^" + "".join(pattern) + "$")



def check_word(word, constraints, illegal_combos, regex):

    # Regex match
    if not regex.match(word):
        return False

    # Excluded letters
    if any(letter in constraints.excluded for letter in word):
        return False

    # Forbidden positions
    for pos, forbidden in constraints.forbidden_positions.items():

        if word[pos] in forbidden:
            return False

    # Required counts
    counts = Counter(word)

    for letter, needed in constraints.required.items():

        if counts[letter] < needed:
            return False

    # Illegal combinations
    if illegal_combos:

        if any(a + b in illegal_combos for a, b in zip(word, word[1:])):
            return False

    return True




def filter_words(words, constraints, illegal_combos):

    regex = build_regex(constraints)

    return [
        word
        for word in words
        if check_word(word, constraints, illegal_combos, regex)
    ]

# =========================================================
# SAVE RESULTS
# =========================================================

def save_words(words):

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:

        for word in words:
            f.write(word + "\n")

# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print("=== Smart Wordle Helper ===")

    illegal_combos = load_illegal_combos()

    while True:

        try:
            word_length = int(input("\nEnter word length: "))
        except ValueError:
            print("Invalid number.")
            continue

        constraints = WordConstraints(word_length)

        use_dictionary = input(
            "Use dictionary? (y/n): "
        ).strip().lower() == "y"

        dictionary = None

        if use_dictionary:

            dictionary = load_dictionary(word_length)

            if not dictionary:
                continue

        turn = 1

        while True:

            print(f"\n========== TURN {turn} ==========")

            # Build legal positions
            legal_positions = build_legal_positions(
                word_length,
                constraints
            )

            estimated = estimate_search_space(
                legal_positions
            )

            print(f"Estimated combinations: {estimated}")

            # Too large to generate
            if not use_dictionary and estimated > MAX_GENERATION_SIZE:

                print(
                    "\nToo many combinations to generate safely."
                )

                print(
                    "Apply more restrictions first."
                )

                constraints.display()

            else:

                # Generate words
                if use_dictionary:

                    possible_words = filter_words(
                        dictionary,
                        constraints,
                        illegal_combos
                    )

                else:

                    generated_words = generate_possible_words(
                        legal_positions
                    )

                    regex = build_regex(constraints)

                    possible_words = [
                        word
                        for word in generated_words
                        if check_word(
                            word,
                            constraints,
                            illegal_combos,
                            regex
                        )
                    ]

                print(
                    f"\nPossible words remaining: "
                    f"{len(possible_words)}"
                )

                save_words(possible_words)

                if len(possible_words) <= 100:
                    print(possible_words)
                else:
                    print(
                        f"Results saved to '{OUTPUT_FILE}'"
                    )

                constraints.display()

            # =================================================
            # USER INPUT
            # =================================================

            command = input(
                "\nEnter guess "
                "(or manual/reset/exit): "
            ).strip().lower()

            if command == "exit":
                return

            if command == "reset":
                break

            # =================================================
            # MANUAL MODE
            # =================================================

            if command == "manual":

                excluded = input(
                    "Excluded letters: "
                ).strip().lower()

                constraints.excluded.update(excluded)

                required = input(
                    "Required letters "
                    "(example a2,b1): "
                ).strip().lower()

                if required:

                    for item in required.split(","):

                        item = item.strip()

                        letter = item[0]
                        count = int(item[1:])

                        constraints.required[letter] = max(
                            constraints.required[letter],
                            count
                        )

                known = input(
                    "Known positions "
                    "(example a0,b3): "
                ).strip().lower()

                if known:

                    for item in known.split(","):

                        item = item.strip()

                        letter = item[0]
                        pos = int(item[1:])

                        constraints.known_positions[pos] = letter

                forbidden = input(
                    "Forbidden positions "
                    "(example a2,b4): "
                ).strip().lower()

                if forbidden:

                    for item in forbidden.split(","):

                        item = item.strip()

                        letter = item[0]
                        pos = int(item[1:])

                        constraints.forbidden_positions[pos].add(letter)

            # =================================================
            # WORDLE FEEDBACK MODE
            # =================================================

            else:

                guess = command

                if len(guess) != word_length:

                    print("Guess length mismatch.")
                    continue

                result = input(
                    "Enter result (g/y/b): "
                ).strip().lower()

                if len(result) != word_length:

                    print("Result length mismatch.")
                    continue

                if any(c not in "gyb" for c in result):

                    print("Only g/y/b allowed.")
                    continue

                constraints.update_from_feedback(
                    guess,
                    result
                )

            turn += 1


if __name__ == "__main__":
    main()
