import itertools
import os
import concurrent.futures
from functools import partial

# Default file paths
DICTIONARY_FILE = "words.txt"
OUTPUT_FILE = "output.txt"
ILLEGAL_COMBOS_FILE = "illegalcombos.txt"

# --- Word checking ---
def load_dictionary(word_length):
    """Load dictionary words of the given length."""
    if not os.path.exists(DICTIONARY_FILE):
        print(f"[!] Dictionary file '{DICTIONARY_FILE}' not found. Using brute force.")
        return None
    with open(DICTIONARY_FILE, "r") as f:
        words = {line.strip().lower() for line in f if len(line.strip()) == word_length}
    print(f"Loaded {len(words)} words from dictionary.")
    return words

def load_illegal_combos():
    """Load forbidden 2-letter combinations."""
    if not os.path.exists(ILLEGAL_COMBOS_FILE):
        return set()
    combos = set()
    with open(ILLEGAL_COMBOS_FILE, "r") as f:
        for line in f:
            pair = line.strip().lower()
            if len(pair) == 2:
                combos.add(pair)
    print(f"Loaded {len(combos)} illegal 2-letter combinations.")
    return combos

def check_word(word, excluded_letters, required_letters, known_positions, forbidden_positions, dictionary=None, illegal_combos=None):
    """Return True if word passes all constraints."""
    if dictionary is not None and word not in dictionary:
        return False
    if any(ch in excluded_letters for ch in word):
        return False
    if not all(ch in word for ch in required_letters):
        return False
    for i, c in enumerate(known_positions):
        if c is not None and word[i] != c:
            return False
    for letter, positions in forbidden_positions.items():
        for pos in positions:
            if pos < len(word) and word[pos] == letter:
                return False
    if illegal_combos:
        for i in range(len(word)-1):
            if word[i:i+2].lower() in illegal_combos:
                return False
    return True

def filter_chunk(chunk, excluded_letters, required_letters, known_positions, forbidden_positions, dictionary, illegal_combos):
    return [
        w for w in chunk
        if check_word(w, excluded_letters, required_letters, known_positions, forbidden_positions, dictionary, illegal_combos)
    ]

def save_words(possible_words):
    with open(OUTPUT_FILE, "w") as f:
        for w in possible_words:
            f.write(w + "\n")

# --- Main Interactive Loop ---
def main():
    print("=== Wordle Helper Interactive (Persistent Constraints) ===")
    word_length = int(input("Enter word length: "))
    use_dict = input("Use dictionary? (y/n): ").strip().lower()

    if use_dict == "y":
        dictionary = load_dictionary(word_length)
        possible_words = list(dictionary)
        use_bruteforce = False
    else:
        dictionary = None
        possible_words = None  # don’t prebuild yet
        use_bruteforce = True

    illegal_combos = load_illegal_combos()

    # Persistent constraints
    master_excluded = set()
    master_required = set()
    master_known_positions = [None] * word_length
    master_forbidden_positions = {}

    turn = 1
    while True:
        print(f"\n--- Turn {turn} ---")
        # User input for this turn
        excluded_letters = set(input("Letters NOT in the word (grays): ").strip().lower())
        required_letters = set(input("Letters that must be in the word (anywhere): ").strip().lower())
        known_positions_input = input(f"Known letters (greens), '_' for unknown: ").strip().lower()
        known_positions = [c if c != "_" else None for c in known_positions_input.ljust(word_length, "_")]

        forbidden_positions = {}
        while True:
            fp = input("Yellow letters with forbidden positions (e.g., r:0,2), blank to finish: ").strip().lower()
            if not fp:
                break
            try:
                letter, positions = fp.split(":")
                positions = [int(p) for p in positions.split(",")] if "," in positions else [int(positions)]
                if letter in forbidden_positions:
                    forbidden_positions[letter].extend(positions)
                else:
                    forbidden_positions[letter] = positions
            except Exception:
                print("Invalid format, try again.")

        # Merge into master constraints
        master_excluded.update(excluded_letters)
        master_required.update(required_letters)
        for i in range(word_length):
            if known_positions[i] is not None:
                master_known_positions[i] = known_positions[i]
        for letter, positions in forbidden_positions.items():
            if letter in master_forbidden_positions:
                master_forbidden_positions[letter].extend(positions)
            else:
                master_forbidden_positions[letter] = positions

        # Build brute force only after we have constraints
        if use_bruteforce and possible_words is None:
            print("[*] Generating brute force candidates on the fly…")
            alphabet = "abcdefghijklmnopqrstuvwxyz"
            # Instead of prebuilding the list, stream and filter immediately
            def generate_candidates():
                for p in itertools.product(alphabet, repeat=word_length):
                    yield "".join(p)

            candidates = generate_candidates()
            # Filter as we stream:
            possible_words = [
                w for w in candidates
                if check_word(w, master_excluded, master_required,
                              master_known_positions, master_forbidden_positions,
                              dictionary, illegal_combos)
            ]
        else:
            # Normal filtering on existing possible_words
            chunk_size = max(1, len(possible_words) // os.cpu_count())
            chunks = [possible_words[i:i+chunk_size] for i in range(0, len(possible_words), chunk_size)]

            with concurrent.futures.ProcessPoolExecutor() as executor:
                func = partial(
                    filter_chunk,
                    excluded_letters=master_excluded,
                    required_letters=master_required,
                    known_positions=master_known_positions,
                    forbidden_positions=master_forbidden_positions,
                    dictionary=dictionary,
                    illegal_combos=illegal_combos
                )
                results = executor.map(func, chunks)

            possible_words = [w for sublist in results for w in sublist]

        save_words(possible_words)

        print(f"\nPossible words remaining: {len(possible_words)}")
        if len(possible_words) <= 20:
            print(possible_words)
        else:
            print("Too many to display. Check output.txt.")

        cont = input("Continue to next turn? (y/n): ").strip().lower()
        if cont != "y":
            break
        turn += 1

    print(f"\nGame ended. Possible words saved to '{OUTPUT_FILE}'.")


if __name__ == "__main__":
    main()
