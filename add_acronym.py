import csv


from flashcards import BUILTIN_DECKS, csv_path, clear_screen, print_mode_banner

MASTER_FILE = "master.csv"
FIELDS = ["acronym", "full_name", "description"]


# 1. File helpers
# 1a. Read every row of a deck file
def read_rows(filename):
    """Read a CSV from the data folder. Return a list of row distionaries."""
    rows = []
    with open(csv_path(filename), mode="r", encoding="utf-8-sig", newline="") as file:
        for row in csv.DictReader(file):
            acronym = (row.get("acronym") or "").strip()
            full_name = (row.get("full_name") or "").strip()
            description = (row.get("description") or "").strip()
            if not acronym and not full_name and not description:
                continue  # skip empty rows
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
    print("\nEnter the new acronym (leave blank to cancel).")
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
            print(f"\n{entry['acronym']} {row['full_name']}) is already listed. Nothing added.")
            input("Press ENTER to continue...")
            return False

    print(f"\n{entry['acronym']} already exists with a different full name:")
    for name in sorted({row["full_name"] for row in matches}):
        print(f"   - {name}")
    answer = input("Add anyway? (y/n): ").strip().lower()
    return answer == "y"


# 4. Main program loop
def main():
    while True:
        clear_screen()
        print_mode_banner("ADD AN ACRONYM")

        label, filename = choose_target_deck()
        if filename is None:
            print("\nNo deck selected. Goodbye.\n")
            return

        entry = ask_for_entry()
        if entry is None:
            continue

        master_rows = read_rows(MASTER_FILE)
        deck_rows = read_rows(filename)
        if not ok_to_add(entry, master_rows + deck_rows):
            continue

        deck_rows.append(entry)
        master_rows.append(entry)
        write_sorted(filename, deck_rows)
        write_sorted(MASTER_FILE, master_rows)

        print(f"\nAdded {entry['acronym']} to {label} and {MASTER_FILE}.")
        input("Press Enter to continue...")


if __name__ == "__main__":
    main()

