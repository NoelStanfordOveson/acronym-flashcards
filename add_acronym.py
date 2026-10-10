import csv


from flashcards import BUILTIN_DECKS, csv_path, clear_screen, print_mode_banner, CARD_WIDTH, overwrite_line

MASTER_FILE = "master.csv"
FIELDS = ["acronym", "full_name", "description"]

# 1a. read_rows
# 1b. write_sorted
# 2. choose_target_deck
# 3a. ask_for_entry
# 3b. ok_to_add
# 3c. confirm_add
# 3d. add_to_deck


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

            extra = row.get(None)                   # unquoted commas split the description
            if extra:
                description = ",".join([description] + extra).strip().strip('"')
                print(f"Repaired {filename} line {reader.line_num}: "
                      f"{acronym} description had unquoted commas.")

            if not acronym and not full_name and not description:
                continue                            # skip empty rows
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
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

# 2. Choose which deck gets the new acronym
def choose_target_deck():
    """Show the built-in decks. Return (label, filename), or (None, None) to exit."""
    while True:
        print("\nWhich deck gets the new acronym?\n")
        for number, (label, filename) in enumerate(BUILTIN_DECKS, start=1):
            print(f"{number}. {label}")
        print("0. Exit")

        raw = input("\nEnter a number: ").strip()
        if raw == "0":
            return None, None
        if raw.isdigit() and 1 <= int(raw) <= len(BUILTIN_DECKS):
            return BUILTIN_DECKS[int(raw) - 1]
        print("That number is not on the list.")

# 3a. Ask for the new acronym's details
def ask_for_entry():
    """Ask for acronym, fullname, and description. Return a dict, or None to cancel."""
    print("\nEnter the new acronym (leave blank to return to the deck menu).\n")
    acronym = input("Acronym:     ").strip()
    if not acronym:
        return None

    full_name = input("Full name:   ").strip()
    description = input("Description: ").strip()

    return {
        "acronym": acronym,
        "full_name": full_name,
        "description": description,
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
            input("Press ENTER to continue...")
            return False

    print(f"\n{entry['acronym']} already exists with a different full name:")
    for name in sorted({row["full_name"] for row in matches}):
        print(f"   - {name}")

    answer = input("Add anyway? (y/n): ").strip().lower()
    if answer != "y":
        print("RESULT: Skipped. No files were changed.")
        input("Press ENTER to continue...")
        return False
    return True

# 3c. Show the new entry and ask before saving
def confirm_add(entry, label):
    """Show what will be saved. Return True for ENTER, False for ESC."""
    # print("\n" + "!" * CARD_WIDTH)
    print("\n\n")
    print(" ⚠️  POINT OF NO RETURN  ⚠️ ".center(CARD_WIDTH, "!"))
    # print("!" * CARD_WIDTH)
    print(f"ACRONYM:     {entry['acronym']}")
    print(f"FULL NAME:   {entry['full_name'] or '(blank)'}")
    print(f"DESCRIPTION: {entry['description'] or '(blank)'}")
    print(f"WRITING TO:  {label} - {MASTER_FILE}")
    print("!" * CARD_WIDTH)
    print("\nAre you SURE? Once it's in, it's in...")
    print("(well, until you open Notepad++ 😏)\n")
    return overwrite_line("ENTER = save it     ESC = forget it") == "enter"



# 3d. Keep adding acronyms to one deck
def add_to_deck(label, filename):
    """Add acronyms to one deck until the acronym is left blank."""
    while True:
        clear_screen()
        print_mode_banner(f"ADDING TO: {label}")

        entry = ask_for_entry()
        if entry is None:
            return                                  # back to the deck menu

        master_rows = read_rows(MASTER_FILE)
        deck_rows = read_rows(filename)

        if not ok_to_add(entry, master_rows + deck_rows):
            continue

        if not confirm_add(entry, label):
            print(f"\nRESULT: Not saved. {filename} and {MASTER_FILE} were NOT changed.")
            input("Press ENTER to continue...")
            continue

        deck_rows.append(entry)
        master_rows.append(entry)
        write_sorted(filename, deck_rows)
        write_sorted(MASTER_FILE, master_rows)

        print(f"\nRESULT: Saved. {entry['acronym']} was added to {filename} and {MASTER_FILE},")
        print("        and both files were re-sorted.")
        input("Press ENTER to continue...")


# 4. Main program loop
def main():
    while True:                                     # deck menu loop
        clear_screen()
        print_mode_banner("ADD AN ACRONYM - DECK LIST")

        label, filename = choose_target_deck()
        if filename is None:
            print("\nNo deck selected. Goodbye.\n")
            return

        add_to_deck(label, filename)                # stays here until a blank acronym

if __name__ == "__main__":
    main()

