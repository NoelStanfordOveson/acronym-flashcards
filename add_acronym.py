import csv


from flashcards import (BUILTIN_DECKS, csv_path, clear_screen, print_mode_banner, 
                        CARD_WIDTH, overwrite_line, read_key, input_or_esc, say_goodbye)

MASTER_FILE = "master.csv"
FIELDS = ["acronym", "full_name", "description"]

# 1a. read_rows
# 1b. write_sorted
# 2. choose_target_deck
# 3a. ask_for_entry
# 3b. ok_to_add
# 3c. confirm_add
# 3d. add_to_deck
# 4. Main program loop


# 1. File helpers
# 1a. Read every row of a deck file
def read_rows(filename):
    """Read a CSV from the data folder. Return a list of row dictionaries."""
    rows = []
    with open(csv_path(filename), mode="r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            acronym = (row.get("acronym") or "").strip()
            full_name = (row.get("full_name") or "").strip()
            description = (row.get("description") or "").strip()

            extra = row.get(None)                                       # unquoted commas split the description
            if extra:
                description = ",".join([description] + extra).strip().strip('"')
                print(f"Repaired {filename} line {reader.line_num}: "
                      f"{acronym} description had unquoted commas.")

            if not acronym and not full_name and not description:
                continue                                                # skip empty rows
            rows.append({
                "acronym": acronym,
                "full_name": full_name,
                "description": description,
            })
    return rows

# 1b. Sort rows by acronym and save them back to the file
def write_sorted(filename, rows):
    """Sort rows by acronym (ignoring capitals), then write the file with its header."""
    rows.sort(key=lambda row: row["acronym"].casefold())
    with open(csv_path(filename), mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

# 2. Choose which deck gets the new acronym
def choose_target_deck():
    """
    Show the built-in decks. 
    Returns (label, filename), 'back' for ESC, or 'quit' for Q.
    """
    deck_keys = [str(number) for number in range(1, len(BUILTIN_DECKS) + 1)]

    clear_screen()
    print_mode_banner("ADD AN ACRONYM - DECK LIST")
    print("\nWhich deck gets the new acronym?\n")
    for number, (label, filename) in enumerate(BUILTIN_DECKS, start=1):
        print(f"{number}. {label}")
    print()
    print("ESC = back     Q = quit")

    choice = read_key(deck_keys + ["esc", "q"])
    if choice == "esc":
        return "back"
    if choice == "q":
        return "quit"
    return BUILTIN_DECKS[int(choice) -1]

# 3a. Ask for the new acronym's details
def ask_for_entry():
    """
    Ask for acronym, full name, and description.
    Returns a dict, or None if ESC was pressed at any prompt.
    """
    print("\nEnter the new acronym.     (ESC = back to the deck list)\n")

    acronym = input_or_esc("Acronym:     ", required=True)
    if acronym is None:
        return None

    full_name = input_or_esc("Full name:   ")
    if full_name is None:
        return None

    description = input_or_esc("Description: ")
    if description is None:
        return None

    return {
        "acronym": acronym.strip(),
        "full_name": full_name.strip(),
        "description": description.strip(),
    }

# 3b. Check for duplicates before adding
def ok_to_add(entry, existing_rows):
    """Return True if the entry should be added, False to skip it."""
    new_acronym = entry["acronym"].casefold()
    new_name = entry["full_name"].casefold()

    matches = [row for row in existing_rows
               if row["acronym"].casefold() == new_acronym]
    if not matches:
        return True

    for row in matches:
        if row["full_name"].casefold() == new_name:
            print(f"\n{entry['acronym']} ({row['full_name']}) is already listed.")
            print("RESULT: Nothing added. No files were changed.")
            return False

    print(f"\n{entry['acronym']} already exists with a different full name:")
    for name in sorted({row["full_name"] for row in matches}):
        print(f"   - {name}")
        print()

    print("Add anyway?  Y = yes     N or ESC = no", end="", flush=True)
    answer = read_key(("y", "n", "esc"))
    print()

    if answer != "y":
        print("RESULT: Skipped. No files were changed.")
        return False
    return True

# 3c. Show the new entry and ask before saving
def confirm_add(entry, label):
    """Show what will be saved. Return True for ENTER, False for ESC."""
    # print("\n" + "!" * CARD_WIDTH)
    print("\n\n")
    print(" ⚠️  CAUTION  ⚠️ ".center(CARD_WIDTH, "*"))
    # print("!" * CARD_WIDTH)
    print(f"ACRONYM:     {entry['acronym']}")
    print(f"FULL NAME:   {entry['full_name'] or '(blank)'}")
    print(f"DESCRIPTION: {entry['description'] or '(blank)'}")
#    print()
    print(f"\nWRITING TO:  {label} - {MASTER_FILE}")
    print("*" * CARD_WIDTH)
    print("\nFiles will be modified and overwritten. Do you really want to proceed?\n")
    # print("(well, until you open Notepad++ 😏)\n")
    return overwrite_line("ENTER = save it     ESC = forget it") == "enter"

# 3d. Keep adding acronyms to one deck
def add_to_deck(label, filename):
    """Add acronyms to one deck. Return 'back' (ESC = deck list) or 'quit' (Q)."""
    while True:
        clear_screen()
        print_mode_banner(f"ADDING TO: {label}")

        entry = ask_for_entry()
        if entry is None:
            return "back"                                               # ESC while typing

        master_rows = read_rows(MASTER_FILE)
        deck_rows = read_rows(filename)

        if ok_to_add(entry, master_rows + deck_rows):
            if confirm_add(entry, label):
                deck_rows.append(entry)
                master_rows.append(entry)
                write_sorted(filename, deck_rows)
                write_sorted(MASTER_FILE, master_rows)
                print(f"\nRESULT: Saved. {entry['acronym']} was added to {filename} and {MASTER_FILE}")
                print("     and both files were re-sorted.")
            else:
                print(f"\nRESULT: Not saved. {filename} and {MASTER_FILE} were NOT changed.")

        action = add_another()
        if action == "esc":
            return "back"
        if action == "q":
            return "quit"

# 3e. After each result: add another, or go back to the deck menu
def add_another():
    """Return 'enter' (add another), 'esc' (deck list), or 'q' (quit)."""
    print()
    print("ENTER = add another     ESC = deck list     Q = quit", end="", flush=True)
    return read_key(("enter", "esc", "q"))


# 4. Main program loop
def main():
    """Run the add-an-acronym tool. Return 'back' (ESC) or 'quit' (Q)"""
    while True:                                                         # deck list loop
        result = choose_target_deck()
        if result in ("back", "quit"):
            return result

        label, filename = result
        if add_to_deck(label, filename) == "quit":
            return "quit"
        # anything else means ESC: loop back to the deck list


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:                                               # Ctrl+C: skip the traceback, exit cleanly
        pass
    say_goodbye()