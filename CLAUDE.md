# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A command-line flashcard app for learning acronyms. Pure Python standard library: no dependencies, no build step, no test suite, no linter config.

## Commands

```bash
py flashcards.py                          # run the app
py check_decks.py                         # audit data/master.csv against the category decks (pass another filename in data/ to override)
```

`comp_csv.ps1` is an older PowerShell version of the same master-vs-categories comparison. It expects the CSVs in the current directory, so it predates the move into `data/`.

## Architecture

- `flashcards.py` is the whole app. `main()` runs two nested loops: a deck loop (`choose_deck()`) and a mode loop (review, random quiz, lookup). Keypress handling in `read_enter_or_esc()` uses `msvcrt` on Windows and `termios` elsewhere.
- Decks are CSVs in `data/` with the header `acronym,full_name,description`. `BUILTIN_DECKS` in `flashcards.py` maps menu labels to filenames. "All built-in decks" merges them and sorts by acronym. "My own CSV" accepts a name inside `data/` or an absolute path.
- `data/master.csv` is the master list. The category decks (certifications, cloud, cybersec, devsec, engineer, management, standards) are meant to partition it. `check_decks.py` reports entries that are missing, extra, mismatched, duplicated, or incomplete.
- `check_decks.py` is standalone and doesn't import `flashcards.py`. It keeps its own copy of `BUILTIN_DECKS`, so the two lists must be updated together.
