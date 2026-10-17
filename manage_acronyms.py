import csv
import ctypes
from ctypes import wintypes

from mez_common import (BUILTIN_DECKS, csv_path, clear_screen, print_mode_banner, print_wrapped,
                        CARD_WIDTH, overwrite_line, read_key, input_or_esc, say_goodbye,
                        load_all_builtin)

MASTER_FILE = "master.csv"
FIELDS = ["acronym", "full_name", "description"]

# 1a. read_rows
# 1b. write_sorted
# 1c. Windows keystroke records (classes)
# 1d. prefill
# 1e. input_prefilled
# 2. choose_target_deck
# 3a. ask_for_entry
# 3b. ok_to_add
# 3c. confirm_add
# 3d. save_entry
# 3e. add_to_deck
# 3f. add_another
# 3g. add_from_lookup
# 3h. add_acronyms
# 4a. show_full_card
# 4b. lookup_acronym
# 4c. lookup_all_decks
# 5a. deck_file_for
# 5b. find_row
# 5c. ask_for_edits
# 5d. confirm_edits
# 5e. find_card_rows
# 5f. edit_card
# 6. Main program loop


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

# 1c. Windows keystroke records (used to pre-fill the console line editor)
class KEY_EVENT_RECORD(ctypes.Structure):
    _fields_ = [("bKeyDown", wintypes.BOOL), ("wRepeatCount", wintypes.WORD),
                ("wVirtualKeyCode", wintypes.WORD), ("wVirtualScanCode", wintypes.WORD),
                ("uChar", wintypes.WCHAR), ("dwControlKeyState", wintypes.DWORD)]

class EVENT_UNION(ctypes.Union):
    _fields_ = [("KeyEvent", KEY_EVENT_RECORD)]

class INPUT_RECORD(ctypes.Structure):
    _fields_ = [("EventType", wintypes.WORD), ("Event", EVENT_UNION)]

# 1d. Put text into the console's typing buffers if it has been typed
def prefill(text):
    """Make the next input() start with this text already typed in."""
    records = (INPUT_RECORD * (len(text) *2))()
    for i, ch in enumerate(text):
        for j, down in enumerate((True, False)):                        # key down, then key up
            record = records[i * 2 + j]
            record.EventType = 0x0001                                   # KEY_EVENT    
            record.Event.KeyEvent.bKeyDown = down
            record.Event.KeyEvent.wRepeatCount = 1
            record.Event.KeyEvent.uChar = ch
    handle = ctypes.windll.kernel32.GetStdHandle(-10)                   # the keyboard input
    written = wintypes.DWORD()
    ctypes.windll.kernel32.WriteConsoleInputW(handle, records, len(records), ctypes.byref(written))

# 1e. Type a line with the old text already filled in, in the console's own editor
def input_prefilled(prompt, default):
    """
    Show the prompt with the old text already typed in, ready to edit.
    Arrows, Home, End and Backspace all work. Returns the edited text. 
    """
    prefill(default.replace("\n", " "))
    return input(prompt).strip()

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
def ask_for_entry(acronym=None):
    """
    Ask for acronym, full name, and description.
    If an acronym is passed in (from a lookup), show it instead of asking.
    Returns a dict, or None if ESC was pressed at any prompt.
    """
    print("\nEnter the new acronym.     (ESC = back to the deck list)\n")

    if acronym is None:
        acronym = input_or_esc("Acronym:     ", required=True)
        if acronym is None:
            return None
    else:
        print(f"Acronym:     {acronym}")

    full_name = input_or_esc("Full name:   ", width=CARD_WIDTH)
    if full_name is None:
        return None

    description = input_or_esc("Description: ", width=CARD_WIDTH)
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
            print("RESULT:  Nothing added. No files were changed.")
            return False

    print(f"\n{entry['acronym']} already exists with a different full name:")
    for name in sorted({row["full_name"] for row in matches}):
        print(f"   - {name}")
    print()

    prompt = "Add anyway?  Y = yes     N or ESC = no"
    print(prompt, end="", flush=True)
    answer = read_key(("y", "n", "esc"))

    if answer == "y":
        chosen = "Add anyway?  Y = yes"
    else:
        chosen = "Add anyway?              N or ESC = no"
    print("\r" + " " * len(prompt) + "\r" + chosen)

    if answer != "y":
        print("RESULT:  Skipped. No files were changed.")
        return False
    return True

# 3c. Show the new entry and ask before saving
def confirm_add(entry, label, filename):
    """Show what will be saved on a clean screen. Return True for ENTER, False for ESC."""
    clear_screen()
    print_mode_banner(f"ADDING TO: {label}")
    print()
    print(" ⚠️  CAUTION  ⚠️ ".center(CARD_WIDTH, "*"))
    print(f"ACRONYM:     {entry['acronym']}")
    print_wrapped("FULL NAME:   ", entry['full_name'] or '(blank)')
    print_wrapped("DESCRIPTION: ", entry['description'] or '(blank)')
    print(f"\nWRITING TO:  {filename} & {MASTER_FILE}")
    print("*" * CARD_WIDTH)
    print("\nFiles will be modified and overwritten. Do you really want to proceed?\n")
    return overwrite_line("ENTER = save it     ESC = forget it") == "enter"

# 3d. Check, confirm and save one new entry to its deck and master
def save_entry(entry, label, filename):
    """
    Check for duplicates, ask to confirm, then add the entry to its deck and master.csv.
    Return True if it was saved, False if not.
    """
    master_rows = read_rows(MASTER_FILE)
    deck_rows = read_rows(filename)

    if not ok_to_add(entry, master_rows + deck_rows):
        return False
    if not confirm_add(entry, label, filename):
        print(f"\nRESULT:  Not saved. {filename} and {MASTER_FILE} were NOT changed.")
        return False

    deck_rows.append(entry)
    master_rows.append(entry)
    write_sorted(filename, deck_rows)
    write_sorted(MASTER_FILE, master_rows)
    print(f"\nRESULT:  Saved. {entry['acronym']} was added to {filename} and {MASTER_FILE}")
    print("     and both files were re-sorted.")
    return True

# 3e. Keep adding acronyms to one deck
def add_to_deck(label, filename):
    """Add acronyms to one deck. Return 'back' (ESC = deck list) or 'quit' (Q)."""
    while True:
        clear_screen()
        print_mode_banner(f"ADDING TO: {label}")

        entry = ask_for_entry()
        if entry is None:
            return "back"                                               # ESC while typing

        save_entry(entry, label, filename)

        action = add_another()
        if action == "esc":
            return "back"
        if action == "q":
            return "quit"

# 3f. After each result: add another, or go back to the deck menu
def add_another():
    """Return 'enter' (add another), 'esc' (deck list), or 'q' (quit)."""
    print()
    print("ENTER = add another     ESC = deck list     Q = quit", end="", flush=True)
    return read_key(("enter", "esc", "q"))

# 3g. Add the one acronym a lookup didn't find
def add_from_lookup(acronym):
    """
    Called from the flashcards lookup when an acronym isn't found.
    Pick a deck, add this one acronym, then go back to the lookup.
    Returns the saved card (a dict), None if nothing was saved, or 'quit' for Q.
    """
    while True:                                                         # deck list loop
        result = choose_target_deck()
        if result == "back":
            return None
        if result == "quit":
            return "quit"

        label, filename = result
        clear_screen()
        print_mode_banner(f"ADDING TO: {label}")

        entry = ask_for_entry(acronym)
        if entry is None:
            continue                                                    # ESC while typing: back to the deck list

        saved = save_entry(entry, label, filename)

        print()
        print("ENTER = back to lookup     Q = quit", end="", flush=True)
        if read_key(("enter", "esc", "q")) == "q":
            return "quit"

        if saved:
            entry["deck"] = label                                       # lookup cards carry their deck name
            return entry
        return None

# 3h. Pick a deck, then keep adding acronyms to it
def add_acronyms():
    """Pick a deck and add acronyms to it. Return 'back' (ESC) or 'quit' (Q)"""
    while True:                                                         # deck list loop
        result = choose_target_deck()
        if result in ("back", "quit"):
            return result

        label, filename = result
        if add_to_deck(label, filename) == "quit":
            return "quit"                                               # anything else means ESC: loop back to the deck list

# 4a. Show a full single flashcard without options
def show_full_card(card, title=None):
    """Show every field at once. An optional title is centered in the top rule."""
    if title:
        print(f" {title} ".center(CARD_WIDTH, "="))
    else:
        print("=" * CARD_WIDTH)
    print(f"DECK:        {card.get('deck', '')}")
    print(f"ACRONYM:     {card['acronym']}")
    print_wrapped("FULL NAME:   ", card["full_name"])
    print_wrapped("DESCRIPTION: ", card["description"])
    print("=" * CARD_WIDTH)

# 4b. Look up a flashcard by acronym
def lookup_acronym(flashcards, deck_name):
    """
    Look up acronyms until the user leaves.
    Return 'back' for ESC or 'quit' for Q.
    """
    while True:
        clear_screen(margin=False)
        print_mode_banner("LOOKUP")
        print()

        query = input_or_esc("Acronym to look up (ESC = menu): ", required=True)
        if query is None:
            return "back"
        query = query.strip()

        query_upper = query.upper()
        matches = [
            card for card in flashcards
            if card["acronym"].strip().upper() == query_upper
        ]

        if not matches:
            print(f'\nNo card found for "{query}".')
        else:
            print(f"\nFound {len(matches)} card(s) for {query_upper}.\n")
            for number, card in enumerate(matches, start=1):
                show_full_card(card, title=f"Match {number} of {len(matches)}")

        keys = ["enter", "esc", "q"]
        prompt = "ENTER = look up another   ESC = menu   Q = quit"
        if not matches:
            keys.append("a")
            prompt = "A = add it   " + prompt

        print()
        print(prompt, end="", flush=True)

        action = read_key(keys)
        if action == "a":
            result = add_from_lookup(query)
            if result == "quit":
                return "quit"
            if result:                                                  # a saved card came back
                if deck_name == "ALL DECKS" or result["deck"] == deck_name:
                    flashcards.append(result)
                    flashcards.sort(key=lambda card: card["acronym"].casefold())
        elif action == "esc":
            return "back"
        elif action == "q":
            return "quit"

# 4c. Look up an acronym across all built-in decks
def lookup_all_decks():
    """Load every built-in deck, then run the lookup. Return 'back' or 'quit'."""
    cards, missing = load_all_builtin()
    if missing:
        print("\nSkipped missing files:", ", ".join(missing))
        input("Press ENTER to continue...")
    return lookup_acronym(cards, "ALL DECKS")

# 5. Edit
# 5a. Find the CSV file for a built-in deck label
def deck_file_for(label):
    """Return the file name for a built-in deck label, or None if it isn't a built-in deck."""
    for deck_label, filename in BUILTIN_DECKS:
        if deck_label == label:
            return filename
    return None

# 5b. Find which row in a file holds this card
def find_row(rows, card):
    """
    Return the position of the first row with the card's acronym AND full name, 
    or None if no row matches.
    """
    for position, row in enumerate(rows):
        if (row["acronym"].casefold() == card["acronym"].casefold()
                and row["full_name"].casefold() == card["full_name"].casefold()):
            return position
    return None

# 5c. Show the edit screen and collect the new values
def ask_for_edits(card):
    """
    Show the hint, the CURRENT card, and an EDITING card with each field pre-filled.
    Return the edited entry as a dict.
    """
    clear_screen()
    print_mode_banner("EDIT AN ACRONYM")
    print("Edit each field, then ENTER. ← → Home End move the cursor.")
    print("ESC clears a field. Nothing is saved until you approve it")
    print("on the next screen.")
    print()
    show_full_card(card, title="CURRENT")
    print(" EDITING ".center(CARD_WIDTH, "="))
    print(f"DECK:        {card['deck']}")

    acronym = ""
    while not acronym:                                                  # a card must have an acronym
        acronym = input_prefilled("ACRONYM:     ", card["acronym"])
    full_name = input_prefilled("FULL NAME:   ", card["full_name"])
    description = input_prefilled("DESCRIPTION: ", card["description"])

    return {"acronym": acronym, "full_name": full_name, "description": description}

# 5d. Show the CURRENT and PROPOSED cards and ask before saving
def confirm_edits(card, new_entry, filename):
    """Show both cards and the CAUTION block. Return True for ENTER, False for ESC."""
    clear_screen()
    print_mode_banner("EDIT AN ACRONYM")
    print()
    show_full_card(card, title="CURRENT")
    show_full_card({**new_entry, "deck": card["deck"]}, title="PROPOSED")
    print()
    print(" ⚠️  CAUTION  ⚠️ ".center(CARD_WIDTH, "*"))
    print(f"WRITING TO:  {filename} & {MASTER_FILE}")
    print("*" * CARD_WIDTH)
    print("\nFiles will be modified and overwritten. Do you really want to proceed?\n")
    return overwrite_line("ENTER = save it     ESC = forget it") == "enter"

# 5e. Load both files and find the card in each; both must be found
def find_card_rows(card, filename):
    """
    Read the card's deck and master.csv and find its row in each.
    Return (deck_rows, deck_position, master_rows, master_position),
    or None (with a message) if either file is missing the card.
    """
    deck_rows = read_rows(filename)
    master_rows = read_rows(MASTER_FILE)
    deck_position = find_row(deck_rows, card)
    master_position = find_row(master_rows, card)

    if deck_position is None:
        print(f"\nRESULT:  Can't edit. {card['acronym']} ({card['full_name']}) wasn't found in {filename}.")
        print("     Nothing was changed. Check deck health can help find the mismatch.")
        return None
    if master_position is None:
        print(f"\nRESULT:  Can't edit. {card['acronym']} ({card['full_name']}) wasn't found in {MASTER_FILE}.")
        print("     Nothing was changed. Check deck health can help find the mismatch.")
        return None

    return deck_rows, deck_position, master_rows, master_position

# 5f. Edit one card: check both files, edit, approve, save
def edit_card(card):
    """
    Edit a built-in card in its deck and in master.csv
    Return the updated card (with its deck), or None if nothing was saved.
    """
    filename = deck_file_for(card["deck"])
    if filename is None:                                                # not a built-in deck
        return None

    found = find_card_rows(card, filename)
    if found is None:                                                   # missing from a file: message already shown
        return None
    deck_rows, deck_position, master_rows, master_position = found

    new_entry = ask_for_edits(card)
    if all(new_entry[field] == card[field] for field in FIELDS):
        print("\nRESULT:  No changes made. Nothing was saved.")
        return None

    if not confirm_edits(card, new_entry, filename):
        print(f"\nRESULT:  Not saved. {filename} and {MASTER_FILE} were NOT changed.")
        return None

    deck_rows[deck_position] = new_entry
    master_rows[master_position] = new_entry
    write_sorted(filename, deck_rows)
    write_sorted(MASTER_FILE, master_rows)
    print(f"\nRESULT:  Saved. {new_entry['acronym']} was updated in {filename} and {MASTER_FILE}")
    print("     and both files were re-sorted.")
    return {**new_entry, "deck": card["deck"]}


# 6. Main program loop
def main():
    """Show the manage-acronyms menu. Return 'back' (ESC) or 'quit' (Q)."""
    while True:
        clear_screen()
        print_mode_banner("MANAGE ACRONYMS")
        print("\nWhat would you like to do?\n")
        print("1. Look up an acronym (all decks)")
        print("2. Add acronyms to a deck")
        print()
        print("ESC = back     Q = quit")

        choice = read_key(("1", "2", "esc", "q"))
        if choice == "esc":
            return "back"
        if choice == "q":
            return "quit"

        if choice == "1":
            result = lookup_all_decks()
        else:
            result = add_acronyms()
        if result == "quit":
            return "quit"                                               # anything else means ESC: show this menu again

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:                                           # Ctrl+C: skip the traceback, exit cleanly
        pass
    say_goodbye()