import csv
import random
import os
import textwrap

CARD_WIDTH = 60                                                     # Width of the flashcard display
TOP_MARGIN =  3                                                     # Number of blank lines at the top of the screen
DATA_FOLDER = "data"                                                # Folder containing category decks

BUILTIN_DECKS = [
    ("AI Security", "ai.csv"),
    ("Certifications", "certs.csv"),
    ("Cloud Security", "cloud.csv"),
    ("Cybersecurity", "cybersec.csv"),
    ("DevSecOps", "devsec.csv"),
    ("IS Engineering", "engineer.csv"),
    ("IS Management", "mgmt.csv"),
    ("Standards/Frameworks", "standards.csv"),
]

# 1a. print_wrapped
# 1b. clear_screen
# 1c. print_mode_banner
# 1d. overwrite_line
# 1e. read_enter_or_esc
# 1f. program_folder
# 1g. csv_path
# 1h. resolve_csv_path
# 1i. get_key
# 1j. read_key
# 1k. input_or_esc
# 2. load_flashcards
# 2a. load_all_builtin
# 3. lookup_acronym
# 4. show_card
# 5. show_full_card
# 6. choose_deck
# 7. say_goodbye
# 8. (Main program loop)


# 1. Helper functions
# 1a. Create a whole-word text wrapping function
def print_wrapped(label, text, width=CARD_WIDTH):
    """Print label + text. Long text wraps by whole words, lined up under the text."""
    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=label,                                       # first line starts with the label
        subsequent_indent=" " * len(label),                         # extra lines line up under the text
        break_long_words=True,                                      # only if one word is longer than the line
        break_on_hyphens=True,                                      # may break after a hyphen already in the word
    )
    print(wrapper.fill(text) or label)

# 1b. Clear the terminal screen
def clear_screen(margin=True):
    """Erase the terminal, then leave a little space at the top."""
    os.system('cls' if os.name == 'nt' else 'clear')    
    if margin:
        print("\n" * TOP_MARGIN)                                    # leave a little space at the top of the screen

# 1c. Print a banner for the choices
def print_mode_banner(title, width=CARD_WIDTH):
    """Print a banner for the mode the user has chosen."""
    print("=" * width)
    print(f" {title} ".center(width, "="))
    print("=" * width)

# 1d. Clear the hint line
def overwrite_line(text):
    """Print text, stay on the line, then erase it after the keypress."""
    print(text, end="", flush=True)
    action = read_enter_or_esc()
    print("\r" + " " * len(text) + "\r", end="", flush=True)
    return action

# 1e. Enter to continue or Esc to go back to menu
def read_enter_or_esc():
    """Wait for ENTER or ESC. Returns 'enter' or 'esc'. Other keys are ignored."""
    return read_key(("enter", "esc"))

# 1f. Find the folder this program lives in
def program_folder():
    """Return the folder where the program is located."""
    return os.path.dirname(os.path.abspath(__file__))

# 1g. Open CSVs from the data folder
def csv_path(filename):
    """Return the full path to a CSV file in the data folder under this program's directory."""
    return os.path.join(program_folder(), DATA_FOLDER, filename)


# 1h. Turn what the user typed into a full path to a CSV file
def resolve_csv_path(name):
    """Turn what the user typed into a full path to a CSV"""
    name = name.strip().strip('"')                                  # Remove whitespace and quotes
    if not name.lower().endswith(".csv"):
        name = name + ".csv"
    if os.path.isabs(name):
        return name
    return csv_path(name)

# 1i. Wait for one key and report which key it was
def get_key():
    """
    Wait for one keypress and return it.
    Returns 'enter', 'esc', or 'backspace' for those keys,
    otherwise the character typed (for example 'q' or '3').
    """
    try:
        import msvcrt                                               # Windows
        while True:
            ch = msvcrt.getwch()
            if ch in ("\x00", "\xe0"):                              # arrow/function keys send two codes
                msvcrt.getwch()                                     # throw away the second code
                continue                                            # and keep waiting for a real key
            break

    except ImportError:
        import sys, tty, termios                                    # mac0S / Linux
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

    if ch in ("\r", "\n"):
        return "enter"
    if ch == "\x1b":
        return "esc"
    if ch in ("\b", "\x7f"):                                        # backspace: Windows sends \b, macOS/Linux \x7f
        return "backspace"
    if ch == "\x03":                                                # Ctrl+C
        raise KeyboardInterrupt
    return ch

# 1j. Wait for one of a few allowed keys
def read_key(allowed):
    """
    Wait until one of the allowed keys is pressed, and return it.
    Letters come back lowercase, so 'Q' and 'q' both return 'q'.
    Any other key is ignored
    """
    while True:
        key = get_key().lower()
        if key in allowed:
            return key

# 1k. Type a line of text; ESC cancels
def input_or_esc(prompt, required=False, width=None):
    """
    Like input(), but ESC cancels.
    If width is given, long text wraps by whole words, lined up under the prompt.
    Returns the typed text when ENTER is pressed, or None for ESC
    """
    print(prompt, end="", flush=True)
    text = ""
    line_start = 0                                                  # where the current screen line starts in text
    indent = " " * len(prompt)                                      # wrapped lines line up under the typing
    while True:
        key = get_key()
        if key == "enter":
            if required and not text.strip():
                continue                                            # nothing typed yet: ignore ENTER
            print()                                                 # move down to the next line
            return text
        if key == "esc":
            print()
            return None
        if key == "backspace":
            if len(text) > line_start:                              # only erase on the current line
                text = text[:-1]                                    # drop the last character
                print("\b \b", end="", flush=True)
            continue
        if len(key) == 1 and key.isprintable():
            if width and len(indent) + len(text) - line_start + 1 > width:  # this key would go past the edge
                if key == " ":                                      # a space: just start the next line
                    text += key
                    print("\n" + indent, end="", flush=True)
                    line_start = len(text)
                    continue
                word_start = text.rfind(" ", line_start) + 1        # where the unfinished word begins
                if word_start > line_start:                         # move the unfinished word down
                    partial = text[word_start:]
                    print("\b \b" * len(partial), end="")
                    print("\n" + indent + partial, end="", flush=True)
                    line_start = word_start
                else:                                               # one huge word: just break it
                    print("\n" + indent, end="", flush=True)
                    line_start = len(text)
            text += key
            print(key, end="", flush=True)

# 2. Load the flashcards from CSV
def load_flashcards(filename, deck_label=None):
    """Load one CSV. Each card remembers which deck it came from."""
    path = filename if os.path.isabs(filename) else csv_path(filename)
    if deck_label is None:
        deck_label = os.path.splitext(os.path.basename(path))[0]    # Use filename without extension as default label

    flashcards = []
    with open(path, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)   # Reads the header row automatically
        for row in reader:
            acronym = (row.get("acronym") or "").strip()
            full_name = (row.get("full_name") or "").strip()
            description = (row.get("description") or "").strip()
            if not acronym and not full_name and not description:
                continue  # Skip empty rows
            flashcards.append({
                "acronym": acronym,
                "full_name": full_name,
                "description": description,
                "deck": deck_label,
            })
    return flashcards

# 2a. Load all flashcards from all built-in decks
def load_all_builtin():
    """Load all flashcards from all built-in decks."""
    cards = []
    missing = []
    for label, filename in BUILTIN_DECKS:
        path = csv_path(filename)
        if os.path.exists(path):
            cards.extend(load_flashcards(filename, label))
        else:
            missing.append(filename)
    cards.sort(key=lambda card: card["acronym"].casefold())
    return cards, missing

# 3. Look up a flashcard by acronym
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
            from add_acronym import add_from_lookup                         # imported here, to avoid a circular import
            result = add_from_lookup(query)
            if result == "quit":
                return "quit"
            if result:                                                      # a saved card came back
                if deck_name == "ALL DECKS" or result["deck"] == deck_name:
                    flashcards.append(result)
                    flashcards.sort(key=lambda card: card["acronym"].casefold())
        elif action == "esc":
            return "back"
        elif action == "q":
            return "quit"

# 4. Show a single flashcard with the option to reveal or go back to menu
def show_card(card, number=None, total=None):
    """ Show one flashcard, reveal on ENTER, or go back to menu on ESC."""
    if number is not None and total is not None:
        print(f" Card {number} of {total} ".center(CARD_WIDTH, "="))
    else:
        print("=" * CARD_WIDTH)
    print(f"DECK:        {card.get('deck', '')}")
    print(f"ACRONYM:     {card['acronym']}")
    if overwrite_line("ENTER = reveal     ESC = menu") == "esc":
        return "esc"

    print_wrapped("FULL NAME:   ", card["full_name"])
    print_wrapped("DESCRIPTION: ", card["description"])
    print("=" * CARD_WIDTH)

    return overwrite_line("ENTER = next card     ESC = menu")

# 5. Show a full single flashcard without options
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

# 6. Flashcard deck chooser
def choose_deck():
    """
    Let the user choose a built-in deck, all decks, or their own CSV.
    Returns (label, cards), or 'back' for ESC, or 'quit' for Q.
    """
    deck_keys = [str(number) for number in range(1, len(BUILTIN_DECKS) + 1)]

    while True:
        clear_screen()
        print_mode_banner("DECK CHOOSER")
        print("\nWhich deck do you want to study?\n")

        for number, (label, filename) in enumerate(BUILTIN_DECKS, start=1):
            exists = " " if os.path.exists(csv_path(filename)) else " (file not found yet)"
            print(f"{number}. {label}{exists}")

        print("A. All Built-in Decks")
        print("C. My own CSV file")
        print()
        print("ESC = back     Q = quit")
            
        choice = read_key(deck_keys + ["a", "c", "esc", "q"])

        if choice == "esc":
            return "back"
        if choice == "q":
            return "quit"

        if choice in deck_keys:
            label, filename = BUILTIN_DECKS[int(choice) - 1]
            if not os.path.exists(csv_path(filename)):
                print(f"\nCreate {filename} in the {DATA_FOLDER} folder first?")
                input("Press Enter to continue...")
                continue
            return label, load_flashcards(filename, label)

        if choice == "a":
            cards, missing = load_all_builtin()
            if missing:
                print("\nSkipped missing files:", ", ".join(missing))
                input("Press ENTER to continue...")
            if not cards:
                print("No decks found yet.")
                input("Press ENTER to continue...")
                continue
            return "ALL DECKS", cards

        if choice == "c":
            print(f"\nType a deck name from the {DATA_FOLDER} folder (.csv is appended for you),")
            print("or a full path such as C:\\Decks\\mine.csv     (ESC = cancel)")

            name = input_or_esc("Deckname or Full Pathname: ")
            if name is None or not name.strip():
                continue

            path = resolve_csv_path(name)
            if not os.path.exists(path):
                print(f"File not found: {path}")
                input("Press ENTER to continue...")
                continue

            deck_label = os.path.basename(path)
            return deck_label, load_flashcards(path, deck_label)

# 7. Sign off block on exit
def say_goodbye():
    """Print the exit message."""
    print()
    print()
    print("Thank you for using the Acronym Finder Flashcards program! Goodbye! 👋")
    print("Made with 💭 by TristanTango73")
    print("\n\n")



# 8. Main program loop
def main():
    """Run the flashcards app. Return 'back' (ESC) or 'quit' (Q)."""
    while True:                                                     # deck loop
        result = choose_deck()
        if result in ("back", "quit"):
            return result
        deck_name, flashcards = result

        if not flashcards:
            print("That deck has no cards yet.")
            input("Press ENTER to continue...")
            continue

        while True:                                                 # mode loop for this deck
            clear_screen()
            print_mode_banner("MAIN MENU")

            print(f"\nDeck: {deck_name}")
            print(f"Loaded {len(flashcards)} flashcards! 🎉\n")
            print("What would you like to do?")
            print("1. Review all cards in order")
            print("2. Random quiz mode")
            print("3. Look up a specific acronym")
            print()
            print("ESC = Choose a different deck     Q = quit")

            choice = read_key(("1", "2", "3", "esc", "q"))

            if choice == "1":
                clear_screen(margin=False)
                print_mode_banner("REVIEW")
                total = len(flashcards)
                for number, card in enumerate(flashcards, start=1):
                    if show_card(card, number=number, total=total) == "esc":
                        break
                        
            elif choice == "2":
                clear_screen(margin=False)
                print_mode_banner("QUIZ")
                quiz_cards = random.sample(flashcards, len(flashcards))  # shuffle the cards
                total = len(quiz_cards)
                for number, card in enumerate(quiz_cards, start=1):
                    if show_card(card, number=number, total=total) == "esc":
                        break

            elif choice == "3":
                if lookup_acronym(flashcards, deck_name) == "quit":
                    return "quit"

            elif choice == "esc":
                break                                               # back to the deck loop

            elif choice == "q":
                return "quit"                                       # leave main() entirely


# This runs the program when you type: py flashcards.py
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:                                       # Ctrl-C: skip the traceback, exit cleanly
        pass
    say_goodbye()