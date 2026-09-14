
from pathlib import Path


def load_dictionary(
    filename: str | Path,
    word_length: int,
) -> set[str]:
    """
    Load words from a dictionary file.

    Only lowercase alphabetic words matching word_length
    are returned.
    """
    if word_length <= 0:
        raise ValueError(
            "Word length must be greater than zero."
        )

    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Dictionary file not found: {path}"
        )

    words: set[str] = set()

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            word = line.strip().lower()

            if len(word) != word_length:
                continue

            if not word.isalpha():
                continue

            words.add(word)

    return words


def load_illegal_combos(
    filename: str | Path,
) -> set[tuple[str, str]]:
    """
    Load illegal adjacent letter combinations.

    Supported formats:

        ab

    or:

        a b

    Blank lines and lines beginning with # are ignored.
    """
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Illegal combinations file not found: {path}"
        )

    combinations: set[tuple[str, str]] = set()

    with path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip().lower()

            if not line or line.startswith("#"):
                continue

            parts = line.split()

            # Format: "ab"
            if len(parts) == 1 and len(parts[0]) == 2:
                combinations.add(
                    (
                        parts[0][0],
                        parts[0][1],
                    )
                )

            # Format: "a b"
            elif len(parts) == 2:
                if (
                    len(parts[0]) == 1
                    and len(parts[1]) == 1
                ):
                    combinations.add(
                        (
                            parts[0],
                            parts[1],
                        )
                    )

    return combinations
