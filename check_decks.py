"""
Compare a master acronym list to the merged built-in flashcard decks.

Put this file next to flashcards.py (the CSV decks live in the data folder), then run:
    py check_decks.py
    py check_decks.py master.csv
    py check_decks.py --master master.csv

Expected CSV columns (same as flashcards.py):
    acronym, full_name, description
"""

import argparse
import csv
import os
from collections import defaultdict

# Same deck list flashcards.py uses for "All built-in decks"
BUILTIN_DECKS = [
    ("Certifications", "certifications.csv"),
    ("Cloud Terms", "cloud.csv"),
    ("Cybersecurity", "cybersec.csv"),
    ("DevSecOps", "devsec.csv"),
    ("IS Engineering", "engineer.csv"),
    ("IS Management", "management.csv"),
    ("Standards/Frameworks", "standards.csv"),
]

REQUIRED_COLUMNS = ("acronym", "full_name", "description")
DATA_FOLDER = "data"


def script_folder():
    """Folder this script lives in (same trick as flashcards.py)."""
    return os.path.dirname(os.path.abspath(__file__))


def csv_path(filename):
    if os.path.isabs(filename):
        return filename
    return os.path.join(script_folder(), DATA_FOLDER, filename)


def norm(text):
    """Strip leftover spaces so ' CIA ' and 'CIA' count as the same."""
    return (text or "").strip()


def key_of(acronym):
    """Compare acronyms case-insensitively: 'Cia' == 'CIA'."""
    return norm(acronym).casefold()


def load_csv(filename, source_label):
    """
    Load one CSV into a list of card dicts.

    Each card keeps:
      - the three fields flashcards.py uses
      - source: which file it came from (for the report)
      - line: spreadsheet row number (header is line 1)
    """
    path = csv_path(filename)
    if not os.path.exists(path):
        return [], f"missing file: {filename}"

    cards = []
    with open(path, mode="r", encoding="utf-8-sig", newline="") as file:
        # utf-8-sig eats a BOM if Excel saved the file
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            return [], f"empty or unreadable: {filename}"

        headers = [norm(name) for name in reader.fieldnames]
        missing_cols = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing_cols:
            return [], (
                f"{filename} is missing columns: {', '.join(missing_cols)}. "
                f"Found: {', '.join(headers)}"
            )

        for line_number, row in enumerate(reader, start=2):
            acronym = norm(row.get("acronym", ""))
            full_name = norm(row.get("full_name", ""))
            description = norm(row.get("description", ""))
            if not acronym and not full_name and not description:
                continue  # skip totally blank rows
            cards.append({
                "acronym": acronym,
                "full_name": full_name,
                "description": description,
                "source": source_label,
                "line": line_number,
            })
    return cards, None


def index_by_acronym(cards):
    """
    Group cards by normalized acronym.

    One acronym can appear more than once (duplicate in one file,
    or the same term living in two decks).
    """
    grouped = defaultdict(list)
    for card in cards:
        grouped[key_of(card["acronym"])].append(card)
    return grouped


def first_nonempty(cards, field):
    for card in cards:
        if card[field]:
            return card[field]
    return ""


def print_section(title, rows):
    print()
    print("=" * 72)
    print(f"{title}  ({len(rows)})")
    print("=" * 72)
    if not rows:
        print("None. Good.")
        return
    for row in rows:
        print(row)


def compare(master_cards, deck_cards):
    master_index = index_by_acronym(master_cards)
    deck_index = index_by_acronym(deck_cards)

    master_keys = set(master_index)
    deck_keys = set(deck_index)

    # --- 1. In master, not in any built-in deck ---
    missing_from_decks = []
    for key in sorted(master_keys - deck_keys):
        card = master_index[key][0]
        missing_from_decks.append(
            f"  {card['acronym'] or '(blank acronym)'}  |  {card['full_name']}"
            f"  [master line {card['line']}]"
        )

    # --- 2. In a deck, not in master ---
    extra_in_decks = []
    for key in sorted(deck_keys - master_keys):
        for card in deck_index[key]:
            extra_in_decks.append(
                f"  {card['acronym'] or '(blank acronym)'}  |  {card['full_name']}"
                f"  [{card['source']} line {card['line']}]"
            )

    # --- 3. Same acronym, different name or description ---
    mismatches = []
    for key in sorted(master_keys & deck_keys):
        master_card = master_index[key][0]
        # If the same acronym is in several decks, compare against each copy
        for deck_card in deck_index[key]:
            name_diff = master_card["full_name"].casefold() != deck_card["full_name"].casefold()
            desc_diff = master_card["description"].casefold() != deck_card["description"].casefold()
            if not name_diff and not desc_diff:
                continue
            mismatches.append(
                f"  {master_card['acronym']}\n"
                f"      MASTER name: {master_card['full_name']}\n"
                f"      DECK   name: {deck_card['full_name']}  ({deck_card['source']} line {deck_card['line']})\n"
                f"      MASTER desc: {master_card['description']}\n"
                f"      DECK   desc: {deck_card['description']}"
            )

    # --- 4. Duplicate acronyms inside the master file ---
    master_dupes = []
    for key, cards in master_index.items():
        if len(cards) > 1:
            lines = ", ".join(str(card["line"]) for card in cards)
            master_dupes.append(
                f"  {cards[0]['acronym']} appears {len(cards)} times in master (lines {lines})"
            )

    # --- 5. Duplicate acronyms inside the merged decks ---
    deck_dupes = []
    for key, cards in deck_index.items():
        if len(cards) > 1:
            places = ", ".join(f"{card['source']} line {card['line']}" for card in cards)
            deck_dupes.append(
                f"  {cards[0]['acronym']} appears {len(cards)} times: {places}"
            )

    # --- 6. Rows that are missing a field ---
    incomplete = []
    for card in master_cards + deck_cards:
        holes = [field for field in REQUIRED_COLUMNS if not card[field]]
        if holes:
            incomplete.append(
                f"  {card['source']} line {card['line']}: missing {', '.join(holes)}"
                f"  (acronym={card['acronym']!r})"
            )

    return {
        "missing_from_decks": missing_from_decks,
        "extra_in_decks": extra_in_decks,
        "mismatches": mismatches,
        "master_dupes": master_dupes,
        "deck_dupes": deck_dupes,
        "incomplete": incomplete,
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compare a master acronym CSV to the merged built-in decks."
    )
    parser.add_argument(
        "master",
        nargs="?",
        default="master.csv",
        help="Master CSV filename (default: master.csv)",
    )
    parser.add_argument(
        "--master",
        dest="master_flag",
        help="Same as the positional filename; use if you prefer --master name.csv",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    master_name = args.master_flag or args.master

    print("Master file:", master_name)
    master_cards, master_error = load_csv(master_name, "master")
    if master_error:
        print("Could not load master:", master_error)
        print("Put the master CSV in the data folder, or pass the full path:")
        print("    py check_decks.py path\\to\\master.csv")
        return

    deck_cards = []
    load_errors = []
    for label, filename in BUILTIN_DECKS:
        cards, error = load_csv(filename, f"{label} ({filename})")
        if error:
            load_errors.append(error)
        else:
            deck_cards.extend(cards)

    print(f"Master rows used: {len(master_cards)}")
    print(f"Merged deck rows: {len(deck_cards)}")
    if load_errors:
        print("Deck load notes:")
        for error in load_errors:
            print("  -", error)

    report = compare(master_cards, deck_cards)

    print_section("IN MASTER, missing from all built-in decks", report["missing_from_decks"])
    print_section("IN A DECK, but not in the master file", report["extra_in_decks"])
    print_section("SAME ACRONYM, different name or description", report["mismatches"])
    print_section("DUPLICATE acronyms in the master file", report["master_dupes"])
    print_section("DUPLICATE acronyms in the merged decks", report["deck_dupes"])
    print_section("INCOMPLETE rows (blank acronym, name, or description)", report["incomplete"])

    problem_count = sum(len(items) for items in report.values())
    print()
    print("-" * 72)
    if problem_count == 0:
        print("All master entries match the merged decks. Nice.")
    else:
        print(f"Finished. {problem_count} item(s) to review.")


if __name__ == "__main__":
    main()
