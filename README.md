# WordleAssist

**WordleAssist** is a pure-Python library for analyzing Wordle-style feedback, managing word constraints, and efficiently finding possible solutions.

It can be used as a standalone program or integrated into other applications such as web APIs.

---

## Features

- Process green, yellow, and gray Wordle feedback
- Track required and excluded letters
- Track known and forbidden letter positions
- Handle minimum and maximum letter counts
- Filter words using a dictionary
- Generate words without a dictionary
- Detect illegal adjacent letter combinations
- Calculate raw search space
- Calculate the exact number of valid solutions
- Efficiently generate valid solutions
- Reusable Python API
- **No third-party dependencies**

---

## Project Structure

```text
WordleAssist/
├── wordle_assist/
│   ├── __init__.py
│   ├── constraints.py
│   ├── dictionary.py
│   ├── engine.py
│   ├── words.txt
│   └── illegalcombos.txt
├── main.py
├── README.md
└── .gitignore
```

### Components

| Module | Description |
|--------|-------------|
| `wordle_assist/constraints.py` | Manages Wordle constraints and validates words |
| `wordle_assist/dictionary.py` | Loads the word dictionary and illegal letter combinations |
| `wordle_assist/engine.py` | Contains the main `WordleEngine` and handles searching, counting, and generating solutions |
| `wordle_assist/__init__.py` | Exposes the public library API |
| `main.py` | Standalone example demonstrating the library |

---

## Installation

WordleAssist has **no external Python dependencies**.

```bash
git clone https://github.com/TheSwiftPython/WordleAssist.git
cd WordleAssist
```

Requires **Python 3.10+**.

---

## Basic Usage

```python
from wordle_assist import WordleEngine

engine = WordleEngine(word_length=5)

engine.apply_feedback(
    "crane",
    ["b", "b", "y", "g", "b"]
)

print(engine.count_possible_words())
print(engine.get_possible_words())
```

### Feedback Values

| Code | Meaning       |
|------|---------------|
| `g`  | Green         |
| `y`  | Yellow        |
| `b`  | Gray / Black  |

---

## Using a Dictionary

```python
from wordle_assist import (
    WordleEngine,
    load_dictionary,
    load_illegal_combos,
)

dictionary = load_dictionary(word_length=5)
illegal_combos = load_illegal_combos()

engine = WordleEngine(
    word_length=5,
    dictionary=dictionary,
    illegal_combos=illegal_combos,
)

engine.apply_feedback(
    "crane",
    ["b", "b", "y", "g", "b"]
)

possible_words = engine.get_possible_words()
print(f"Found {len(possible_words)} possible words")
```

---

## Multiple Guesses

Multiple guesses can be applied to the same engine. Each guess further restricts the possible solutions.

```python
engine.apply_feedback(
    "crane",
    ["b", "b", "y", "g", "b"]
)

engine.apply_feedback(
    "sloth",
    ["b", "y", "b", "g", "b"]
)

print(engine.count_possible_words())
```

---

## Counting and Generating

WordleAssist separates **counting** solutions from **generating** them.

### Exact Count

```python
count = engine.count_possible_words()
```

This calculates the exact number of valid solutions without generating the entire result list.

### Generate Solutions

```python
words = engine.get_possible_words()
```

The engine limits generation when the number of valid solutions becomes too large.  
Generation can be forced when necessary:

```python
words = engine.get_possible_words(force=True)
```

> The generation limit applies to the number of **actual valid solutions**, not the theoretical search space.

**Example:**

| Metric              | Value     |
|---------------------|-----------|
| Raw search space    | 3,184,020 |
| Exact valid words   | 40        |
| Generated words     | 40        |

The 40 valid words can be generated without forcing the search.

---

## Search Space

WordleAssist provides two search-space measurements.

### Raw Search Space

```python
raw_count = engine.estimate_raw_search_space()
```

The theoretical number of combinations remaining after positional constraints.

### Exact Valid Count

```python
valid_count = engine.count_possible_words()
```

The exact number of valid solutions after all constraints are applied.

> `estimate_search_space()` is also available for compatibility and returns the exact valid count.

---

## Dictionary-Free Generation

WordleAssist can generate combinations without a dictionary.

```python
from wordle_assist import WordleEngine

engine = WordleEngine(
    word_length=5,
    illegal_combos={
        ("q", "x"),
        ("q", "z"),
    },
)

engine.apply_feedback(
    "crane",
    ["b", "b", "y", "g", "b"]
)

print(engine.count_possible_words())
```

This is useful for analyzing the underlying search space independently of a specific word list.

---

## Illegal Letter Combinations

`illegalcombos.txt` contains adjacent letter combinations that should not occur in generated words.

**Examples:**
- `qx`
- `qz`
- `jx`

These combinations are used during both counting and generation.

---

## Public API

The main classes and functions are exposed directly from the package:

```python
from wordle_assist import (
    WordConstraints,
    WordleEngine,
    load_dictionary,
    load_illegal_combos,
)
```

Applications can use the public API without depending on the package's internal modules.

---

## Web Application Integration

WordleAssist can be used as the backend engine for a web application.

```python
from wordle_assist import WordleEngine

engine = WordleEngine(
    word_length=5,
    dictionary=dictionary,
    illegal_combos=illegal_combos,
)

for guess in guesses:
    engine.apply_feedback(
        guess["word"],
        guess["result"],
    )

analysis = engine.get_analysis()
possible_words = engine.get_possible_words()
```

The library has **no dependency** on FastAPI, Flask, React, or any other web framework.

---

## Performance

WordleAssist uses different approaches for counting and generating solutions:

- **Dynamic programming** for efficient exact counting
- **Constraint-based backtracking** for solution generation
- Early pruning of invalid combinations
- Dictionary filtering when a dictionary is provided
- Illegal-combination checks during generation

This allows large theoretical search spaces to be analyzed without unnecessarily generating every possible combination.

---

## Running the Example

Run the included standalone program with:

```bash
python main.py
```

---

## Requirements

- Python 3.10+
- No third-party dependencies

---

## License

This project is currently intended for personal and educational use.
