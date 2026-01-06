import itertools
import concurrent.futures
import os

# --- CONFIGURABLE CONSTRAINTS ---
# Excluded letters (GRAY letters in Wordle)
# Example: excluded_letters = set("abc")  → words cannot contain a, b, or c
excluded_letters = set("spektogh")

# Required letters (must appear at least once in the word, anywhere)
# Example: required_letters = set("rt")  → words must include 'r' and 't'
required_letters = set("au")

# Known positions (GREEN letters in Wordle)
# Use None for unknown positions.
# Example: known_positions = [None, "a", None, None, "e"]  → 2nd letter is 'a', 5th is 'e'
known_positions = [None, None, None, "a", None]

# Forbidden positions (YELLOW letters in Wordle)
# Format: { "letter": [pos1, pos2, ...], ... }
# Example: forbidden_positions = { "r": [0, 2], "t": [4] }
# → 'r' cannot be in position 0 or 2, 't' cannot be in position 4
forbidden_positions = {"u":[2]}

# Word length (Wordle default is 5)
word_length = 5
alphabet = "abcdefghijklmnopqrstuvwxyz"

# --- DICTIONARY OPTION ---
# True = only keep real words from words.txt
# False = brute-force all possible combinations
USE_DICTIONARY = True
DICTIONARY_FILE = "words.txt"


def load_dictionary():
    """Load dictionary words if enabled."""
    if not USE_DICTIONARY:
        return None
    if not os.path.exists(DICTIONARY_FILE):
        print(f"[!] Dictionary file '{DICTIONARY_FILE}' not found. Using brute force mode.")
        return None
    with open(DICTIONARY_FILE, "r") as f:
        words = {line.strip().lower() for line in f if line.strip()}
    return words


def check_word(word: str, dictionary=None) -> str | None:
    """Return the word if it matches constraints, else None."""

    # Dictionary check (only if USE_DICTIONARY is True)
    if USE_DICTIONARY and dictionary is not None and word not in dictionary:
        return None

    # Excluded letters
    if excluded_letters and any(ch in excluded_letters for ch in word):
        return None

    # Required letters
    if required_letters and not all(ch in word for ch in required_letters):
        return None

    # Known positions (greens)
    for i in range(word_length):
        if known_positions[i] is not None and word[i] != known_positions[i]:
            return None

    # Forbidden positions (yellows)
    for letter, positions in forbidden_positions.items():
        for pos in positions:
            if pos < word_length and word[pos] == letter:
                return None

    return word


def process_chunk(start_letter: str, dictionary=None) -> list[str]:
    """Generate all words starting with a given letter and filter them."""
    results = []
    for combo in itertools.product(alphabet, repeat=word_length - 1):
        word = start_letter + "".join(combo)
        w = check_word(word, dictionary)
        if w is not None:
            results.append(w)
    return results


if __name__ == "__main__":
    print("Generating possible words...")

    dictionary = load_dictionary()

    all_words = []

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_chunk, letter, dictionary) for letter in alphabet]
        for f in concurrent.futures.as_completed(futures):
            all_words.extend(f.result())

    print(f"Found {len(all_words)} possible words.")

    with open("output.txt", "w") as f:
        for w in all_words:
            f.write(w + "\n")

    print("Results saved to output.txt")
