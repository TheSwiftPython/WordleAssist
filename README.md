# WordleAssist

A Python library for analyzing Wordle-style word constraints, filtering possible words, and efficiently generating valid word combinations.

WordleAssist is designed to work both as a standalone Python program and as a reusable library that can be integrated into other applications, such as web applications and APIs.

## Features

- Track Wordle-style green, yellow, and gray feedback
- Maintain excluded letters
- Track required letters and minimum counts
- Track maximum letter counts
- Track known letter positions
- Track forbidden letter positions
- Filter a dictionary of possible words
- Generate valid words without a dictionary
- Account for illegal adjacent letter combinations
- Calculate the theoretical search space
- Calculate the exact number of valid solutions without generating them
- Avoid unnecessarily generating extremely large result sets
- Reusable Python API
- Suitable for integration with web applications and other programs
- No third-party Python dependencies

## Project Structure

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
Package Components
wordle_assist/constraints.py

Contains the WordConstraints class, which maintains the current Wordle constraints.

It handles:

Excluded letters
Required letters
Minimum letter counts
Maximum letter counts
Known positions
Forbidden positions
Word validation
wordle_assist/dictionary.py

Provides functions for loading:

Word dictionaries
Illegal letter combinations

The default dictionary files are stored inside the wordle_assist package.

wordle_assist/engine.py

Contains the main WordleEngine class.

The engine is responsible for:

Applying Wordle feedback
Calculating search spaces
Counting valid solutions
Generating possible words
Filtering dictionary words
Generating combinations when no dictionary is used
wordle_assist/__init__.py

Exposes the primary public API for the package.

main.py

A standalone example/CLI that demonstrates using the WordleAssist library.

Installation

WordleAssist currently has no external Python dependencies.

Clone the repository:

git clone https://github.com/YOUR_USERNAME/WordleAssist.git
cd WordleAssist

The package can then be imported directly from the repository.

Basic Usage
from wordle_assist import WordleEngine

engine = WordleEngine(word_length=5)

engine.apply_feedback(
    "crane",
    ["b", "b", "y", "g", "b"]
)

print(engine.count_possible_words())
print(engine.get_possible_words())

Feedback characters are:

g — Green: correct letter in the correct position
y — Yellow: correct letter in the wrong position
b — Gray/Black: letter is not present or exceeds its allowed count

For example:

CRANE
⬛ ⬛ 🟨 🟩 ⬛

can be represented as:

["b", "b", "y", "g", "b"]
Using a Dictionary

WordleAssist can use a dictionary to restrict results to known words.

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

for word in possible_words:
    print(word)

The included words.txt file is used when loading the default dictionary.

Applying Multiple Guesses

Multiple guesses can be applied to the same engine.

from wordle_assist import WordleEngine, load_dictionary

engine = WordleEngine(
    word_length=5,
    dictionary=load_dictionary(word_length=5),
)

engine.apply_feedback(
    "crane",
    ["b", "b", "y", "g", "b"]
)

engine.apply_feedback(
    "sloth",
    ["b", "y", "b", "g", "b"]
)

print(engine.count_possible_words())

Each new guess further restricts the possible solutions.

Counting vs. Generating

WordleAssist separates counting possible solutions from generating the solutions themselves.

Exact Count
count = engine.count_possible_words()

print(count)

This calculates the exact number of valid words without necessarily creating a list containing every result.

This is useful when the search space is large.

Generate Results
words = engine.get_possible_words()

for word in words:
    print(word)

By default, WordleAssist limits generation to avoid unnecessarily creating extremely large result sets.

If the exact number of valid results exceeds the generation limit, generation can be explicitly forced:

words = engine.get_possible_words(force=True)

The generation limit applies to the actual number of valid results, not the theoretical search space.

For example:

Raw search space: 3,184,020
Exact valid words: 40
Generated words: 40

The engine can still generate the 40 valid words without requiring force=True.

Search Space Estimation

WordleAssist provides two different measurements.

Raw Search Space
raw_count = engine.estimate_raw_search_space()

This represents the theoretical number of combinations that satisfy the positional constraints before checking whether the combinations are actual dictionary words.

Exact Valid Count
valid_count = engine.count_possible_words()

This represents the exact number of valid solutions after applying all constraints.

For compatibility, estimate_search_space() is also available:

valid_count = engine.estimate_search_space()

estimate_search_space() returns the exact valid count.

Dictionary-Free Generation

WordleAssist can also operate without a dictionary.

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

When no dictionary is supplied, the engine generates combinations based on the active constraints and illegal letter combinations.

This can be useful for analyzing the underlying search space independently of a particular word list.

Illegal Letter Combinations

illegalcombos.txt contains adjacent letter combinations that should not occur in generated words.

For example:

qx
qz
jx

Each entry represents an adjacent pair of letters.

The engine uses these combinations during both counting and generation.

This allows dictionary-free generation to avoid obviously invalid combinations without having to construct every possible string first.

Constraints

The current constraints can be inspected directly:

constraints = engine.get_constraints_dict()

print(constraints)

The library uses Python snake_case naming for its internal API.

A typical result looks like:

{
    "excluded": ["a", "e"],
    "required": {
        "r": 1
    },
    "maximum": {},
    "known_positions": {
        2: "r"
    },
    "forbidden_positions": {
        1: ["r"]
    }
}
Analysis

The engine also provides a combined analysis result:

analysis = engine.get_analysis()

print(analysis)

Example:

{
    "possible_count": 40,
    "raw_search_space": 3184020,
    "constraints": {
        "excluded": [],
        "required": {},
        "maximum": {},
        "known_positions": {},
        "forbidden_positions": {},
    },
}

The analysis provides both the theoretical search space and the exact number of valid solutions.

Resetting the Engine

The engine can be reset and reused:

engine.reset()

This clears the current constraints and cached results.

A new set of guesses can then be applied.

Public API

The primary public classes and functions are exposed from the package root:

from wordle_assist import (
    WordConstraints,
    WordleEngine,
    load_dictionary,
    load_illegal_combos,
)

This allows applications to use WordleAssist without depending on the package's internal module structure.

For example, an external application can simply use:

from wordle_assist import WordleEngine

rather than importing directly from:

from wordle_assist.engine import WordleEngine

This makes the package easier to integrate into other applications and allows its internal implementation to change without requiring consumers to change their imports.

Web Application Integration

WordleAssist is designed to be usable as the backend engine for a web application.

For example, a FastAPI application can create a new engine for each request:

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

The library itself does not depend on FastAPI, Flask, React, or any other web framework.

This keeps the Wordle logic independent from the application using it.

Performance

WordleAssist uses different algorithms depending on how it is being used.

When counting generated combinations, the engine uses dynamic programming rather than constructing every possible word.

When generating results, the engine uses constraint-based backtracking and prunes invalid branches as early as possible.

Dictionary mode avoids generating combinations that are not present in the supplied dictionary.

This allows the engine to distinguish between:

Theoretical search space
        ↓
Constraint filtering
        ↓
Exact valid count
        ↓
Optional result generation

This is particularly useful when the theoretical search space is very large but only a small number of valid words remain.

Running the Example Program

The repository includes main.py as a standalone demonstration.

Run it with:

python main.py

The example program uses the wordle_assist package and demonstrates the engine independently from any web application.

Requirements
Python 3.10 or newer
No third-party Python packages required

The project is intended to remain lightweight and dependency-free.

Development

The package is organized so that the core Wordle logic remains independent from the command-line interface and external applications.

wordle_assist/
    Core reusable library

main.py
    Example/CLI consumer

Applications that integrate WordleAssist should use the public API exposed by wordle_assist.