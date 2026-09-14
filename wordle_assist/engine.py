from functools import lru_cache
from string import ascii_lowercase

from .constraints import WordConstraints


class WordleEngine:
    """
    Reusable Wordle solving engine.

    The engine can operate in two modes:

    1. Dictionary mode
       Search an existing dictionary.

    2. Generation mode
       Generate all alphabetic combinations that satisfy the
       current Wordle constraints.

    Exact counting is performed independently of word generation.
    """

    DEFAULT_MAX_GENERATION_SIZE = 500_000

    def __init__(
        self,
        word_length: int,
        dictionary: set[str] | None = None,
        illegal_combos: set[tuple[str, str]] | None = None,
        max_generation_size: int = DEFAULT_MAX_GENERATION_SIZE,
    ):
        if word_length <= 0:
            raise ValueError(
                "Word length must be greater than zero."
            )

        self.word_length = word_length

        self.dictionary = (
            {word.lower() for word in dictionary}
            if dictionary is not None
            else None
        )

        self.illegal_combos = {
            (
                first.lower(),
                second.lower(),
            )
            for first, second in (illegal_combos or set())
        }

        self.max_generation_size = max_generation_size

        self.constraints = WordConstraints(word_length)

        self._possible_words_cache: list[str] | None = None
        self._exact_count_cache: int | None = None
        self._raw_count_cache: int | None = None

    # =========================================================
    # PUBLIC STATE
    # =========================================================

    def reset(self) -> None:
        self.constraints.reset()
        self._invalidate_cache()

    def apply_feedback(
        self,
        guess: str,
        result: str,
    ) -> None:
        guess = guess.strip().lower()
        result = result.strip().lower()

        if len(guess) != self.word_length:
            raise ValueError(
                f"Guess must be exactly {self.word_length} letters."
            )

        if len(result) != self.word_length:
            raise ValueError(
                f"Result must be exactly {self.word_length} characters."
            )

        self.constraints.update_from_feedback(
            guess,
            result,
        )

        self._invalidate_cache()

    # =========================================================
    # SEARCH SPACE
    # =========================================================

    def estimate_raw_search_space(self) -> int:
        """
        Returns the raw number of combinations remaining after
        applying position-level constraints.

        This does NOT account for:
        - required letter counts
        - maximum letter counts
        - illegal adjacent combinations
        - dictionary membership
        """
        if self._raw_count_cache is not None:
            return self._raw_count_cache

        legal_positions = self._build_legal_positions()

        total = 1

        for letters in legal_positions:
            total *= len(letters)

            if total == 0:
                break

        self._raw_count_cache = total

        return total

    def count_possible_words(self) -> int:
        """
        Returns the exact number of valid possible words.

        This does NOT generate or store the words.

        Dictionary mode:
            Counts matching dictionary entries.

        Generation mode:
            Uses dynamic programming to count valid combinations.
        """
        if self._exact_count_cache is not None:
            return self._exact_count_cache

        if self.dictionary is not None:
            count = 0

            for word in self.dictionary:
                if self.constraints.validate_word(word):
                    if self._contains_no_illegal_combo(word):
                        count += 1

            self._exact_count_cache = count
            return count

        count = self._count_generated_words()

        self._exact_count_cache = count

        return count

    def estimate_search_space(self) -> int:
        """
        Backwards-compatible public API.

        This now returns the EXACT number of valid possible words.

        Use estimate_raw_search_space() if you want the raw
        computational search space instead.
        """
        return self.count_possible_words()

    # =========================================================
    # WORD GENERATION
    # =========================================================

    def get_possible_words(
        self,
        force: bool = False,
    ) -> list[str]:
        """
        Generate and return all valid possible words.

        `force` only matters when the exact number of possible
        words exceeds max_generation_size.

        Importantly, a huge raw search space does NOT require force
        if the actual number of valid words is small.
        """
        if self._possible_words_cache is not None:
            return list(self._possible_words_cache)

        exact_count = self.count_possible_words()

        if (
            exact_count > self.max_generation_size
            and not force
        ):
            raise RuntimeError(
                f"Generation would produce approximately "
                f"{exact_count:,} valid words, which exceeds "
                f"the maximum allowed generation size of "
                f"{self.max_generation_size:,}. "
                f"Use force=True to continue."
            )

        if self.dictionary is not None:
            words = [
                word
                for word in self.dictionary
                if self.constraints.validate_word(word)
                and self._contains_no_illegal_combo(word)
            ]

            words.sort()

        else:
            words = self._generate_words()

        self._possible_words_cache = words

        return list(words)

    # =========================================================
    # ANALYSIS
    # =========================================================

    def get_analysis(self) -> dict:
        """
        Returns all useful search information without generating
        the complete result list.
        """
        return {
            "possible_count": self.count_possible_words(),
            "raw_search_space": self.estimate_raw_search_space(),
            "constraints": self.get_constraints_dict(),
        }

    def get_constraints_dict(self) -> dict:
        return self.constraints.to_dict()

    # =========================================================
    # POSITION BUILDING
    # =========================================================

    def _build_legal_positions(self) -> list[list[str]]:
        """
        Build the legal letters for every position.

        This applies:
        - excluded letters
        - green letters
        - position-specific forbidden letters
        - maximum count == 0
        """
        positions: list[list[str]] = []

        for position in range(self.word_length):
            known = self.constraints.known_positions.get(position)

            if known is not None:
                candidates = [known]
            else:
                candidates = list(ascii_lowercase)

            legal = [
                letter
                for letter in candidates
                if self.constraints.is_letter_allowed(
                    letter,
                    position,
                )
            ]

            positions.append(legal)

        return positions

    # =========================================================
    # EXACT GENERATION COUNT
    # =========================================================

    def _count_generated_words(self) -> int:
        """
        Exact dynamic-programming count.

        Words are processed from left to right so illegal adjacent
        combinations can be checked immediately.

        The DP state contains:
        - current position
        - previous letter
        - current required-letter counts

        This means the engine can calculate an exact answer without
        constructing every candidate string.
        """
        legal_positions = self._build_legal_positions()

        if any(not letters for letters in legal_positions):
            return 0

        required_letters = tuple(
            sorted(self.constraints.required.keys())
        )

        required_targets = tuple(
            self.constraints.required[letter]
            for letter in required_letters
        )

        required_index = {
            letter: index
            for index, letter in enumerate(required_letters)
        }

        maximums = self.constraints.maximum

        illegal_combos = self.illegal_combos

        @lru_cache(maxsize=None)
        def count(
            position: int,
            previous_letter: str,
            counts: tuple[int, ...],
        ) -> int:
            if position == self.word_length:
                for current, target in zip(
                    counts,
                    required_targets,
                ):
                    if current < target:
                        return 0

                return 1

            total = 0

            for letter in legal_positions[position]:
                if previous_letter:
                    if (
                        previous_letter,
                        letter,
                    ) in illegal_combos:
                        continue

                index = required_index.get(letter)

                new_counts = counts

                if index is not None:
                    current_count = counts[index]
                    maximum = maximums.get(letter)

                    if maximum is not None:
                        if current_count >= maximum:
                            continue

                    new_values = list(counts)
                    new_values[index] += 1
                    new_counts = tuple(new_values)

                total += count(
                    position + 1,
                    letter,
                    new_counts,
                )

            return total

        initial_counts = tuple(
            0 for _ in required_letters
        )

        return count(
            0,
            "",
            initial_counts,
        )

    # =========================================================
    # ACTUAL WORD GENERATION
    # =========================================================

    def _generate_words(self) -> list[str]:
        legal_positions = self._build_legal_positions()

        if any(not letters for letters in legal_positions):
            return []

        results: list[str] = []
        current = [""] * self.word_length

        required = self.constraints.required
        maximums = self.constraints.maximum

        counts: dict[str, int] = {}

        def search(position: int) -> None:
            if position == self.word_length:
                for letter, minimum in required.items():
                    if counts.get(letter, 0) < minimum:
                        return

                word = "".join(current)

                if self._contains_no_illegal_combo(word):
                    results.append(word)

                return

            for letter in legal_positions[position]:
                current_count = counts.get(letter, 0)

                maximum = maximums.get(letter)

                if (
                    maximum is not None
                    and current_count >= maximum
                ):
                    continue

                # Check adjacent illegal combinations immediately.
                if position > 0:
                    previous = current[position - 1]

                    if (
                        previous,
                        letter,
                    ) in self.illegal_combos:
                        continue

                # Forward-check required letters.
                counts[letter] = current_count + 1
                current[position] = letter

                if self._requirements_still_possible(
                    position + 1,
                    counts,
                    legal_positions,
                ):
                    search(position + 1)

                if current_count:
                    counts[letter] = current_count
                else:
                    counts.pop(letter, None)

                current[position] = ""

        search(0)

        results.sort()

        return results

    # =========================================================
    # FORWARD CHECKING
    # =========================================================

    def _requirements_still_possible(
        self,
        next_position: int,
        counts: dict[str, int],
        legal_positions: list[list[str]],
    ) -> bool:
        """
        Determines whether every required letter can still reach
        its minimum count with the remaining positions.
        """
        remaining_positions = range(
            next_position,
            self.word_length,
        )

        for letter, minimum in self.constraints.required.items():
            current = counts.get(letter, 0)

            if current >= minimum:
                continue

            needed = minimum - current

            possible_slots = 0

            maximum = self.constraints.maximum.get(letter)

            if maximum is not None:
                if current >= maximum:
                    return False

            for position in remaining_positions:
                if letter in legal_positions[position]:
                    possible_slots += 1

                    if possible_slots >= needed:
                        break

            if possible_slots < needed:
                return False

        return True

    # =========================================================
    # ILLEGAL COMBINATIONS
    # =========================================================

    def _contains_no_illegal_combo(
        self,
        word: str,
    ) -> bool:
        if not self.illegal_combos:
            return True

        for first, second in zip(
            word,
            word[1:],
        ):
            if (first, second) in self.illegal_combos:
                return False

        return True

    # =========================================================
    # CACHE
    # =========================================================

    def _invalidate_cache(self) -> None:
        self._possible_words_cache = None
        self._exact_count_cache = None
        self._raw_count_cache = None