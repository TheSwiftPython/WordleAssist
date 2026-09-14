
from collections import defaultdict


class WordConstraints:
    """
    Stores all Wordle constraints for a single puzzle.
    """

    def __init__(self, word_length: int):
        if word_length <= 0:
            raise ValueError(
                "Word length must be greater than zero."
            )

        self.word_length = word_length

        # Letters known to be absent entirely.
        self.excluded: set[str] = set()

        # Minimum number of occurrences required.
        self.required: dict[str, int] = defaultdict(int)

        # Maximum number of occurrences allowed.
        self.maximum: dict[str, int] = {}

        # Position -> known green letter.
        self.known_positions: dict[int, str] = {}

        # Position -> letters that cannot appear there.
        self.forbidden_positions: dict[int, set[str]] = defaultdict(set)

    def reset(self) -> None:
        self.excluded.clear()
        self.required.clear()
        self.maximum.clear()
        self.known_positions.clear()
        self.forbidden_positions.clear()

    def update_from_feedback(
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

        if not guess.isalpha():
            raise ValueError(
                "Guess must contain letters only."
            )

        if any(
            char not in {"g", "y", "b"}
            for char in result
        ):
            raise ValueError(
                "Result must contain only g, y, and b."
            )

        positive_counts: dict[str, int] = defaultdict(int)
        has_gray: set[str] = set()

        for letter, status in zip(guess, result):
            if status in {"g", "y"}:
                positive_counts[letter] += 1
            else:
                has_gray.add(letter)

        # Apply positional constraints.
        for position, (letter, status) in enumerate(
            zip(guess, result)
        ):
            if status == "g":
                self.known_positions[position] = letter

            elif status == "y":
                self.forbidden_positions[position].add(letter)

            elif status == "b":
                self.forbidden_positions[position].add(letter)

        # Apply minimum counts.
        for letter, count in positive_counts.items():
            self.required[letter] = max(
                self.required.get(letter, 0),
                count,
            )

        # Handle gray duplicates correctly.
        for letter in has_gray:
            positive_count = positive_counts.get(letter, 0)

            if positive_count > 0:
                self.maximum[letter] = positive_count
            else:
                self.maximum[letter] = 0
                self.excluded.add(letter)

        # Positive feedback means the letter is not globally excluded.
        for letter in positive_counts:
            self.excluded.discard(letter)

    def is_letter_allowed(
        self,
        letter: str,
        position: int,
    ) -> bool:
        letter = letter.lower()

        if letter in self.excluded:
            return False

        known = self.known_positions.get(position)

        if known is not None and letter != known:
            return False

        if letter in self.forbidden_positions.get(
            position,
            set(),
        ):
            return False

        maximum = self.maximum.get(letter)

        if maximum == 0:
            return False

        return True

    def validate_word(
        self,
        word: str,
    ) -> bool:
        word = word.lower()

        if len(word) != self.word_length:
            return False

        if not word.isalpha():
            return False

        counts: dict[str, int] = defaultdict(int)

        for position, letter in enumerate(word):
            if not self.is_letter_allowed(
                letter,
                position,
            ):
                return False

            counts[letter] += 1

        for letter, minimum in self.required.items():
            if counts.get(letter, 0) < minimum:
                return False

        for letter, maximum in self.maximum.items():
            if counts.get(letter, 0) > maximum:
                return False

        return True

    def to_dict(self) -> dict:
        """
        Return the library's native Python representation.

        Python library APIs consistently use snake_case.
        """
        return {
            "excluded": sorted(self.excluded),

            "required": dict(
                sorted(self.required.items())
            ),

            "maximum": dict(
                sorted(self.maximum.items())
            ),

            "known_positions": {
                str(position): letter
                for position, letter in sorted(
                    self.known_positions.items()
                )
            },

            "forbidden_positions": {
                str(position): sorted(letters)
                for position, letters in sorted(
                    self.forbidden_positions.items()
                )
            },
        }

    def __repr__(self) -> str:
        return (
            "WordConstraints("
            f"word_length={self.word_length}, "
            f"excluded={sorted(self.excluded)}, "
            f"required={dict(self.required)}, "
            f"maximum={self.maximum}, "
            f"known_positions={self.known_positions}, "
            f"forbidden_positions="
            f"{dict(self.forbidden_positions)})"
        )