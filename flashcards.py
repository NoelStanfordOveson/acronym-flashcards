import csv
import random
import os
import textwrap

CARD_WIDTH = 60                         # Width of the flashcard display
TOP_MARGIN =  3                         # Number of blank lines at the top of the screen
DATA_FOLDER = "data"

BUILTIN_DECKS = [
    ("Certifications", "certifications.csv"),
    ("Cloud Terms", "cloud.csv"),
    ("Cybersecurity", "cybersec.csv"),
    ("DevSecOps", "devsec.csv"),
    ("IS Engineering", "engineer.csv"),
    ("IS Management", "management.csv"),
    ("Standards/Frameworks", "standards.csv"),
]



# 1. Helper functions
# 1a. Create a whole-word text wrapping function
def print_wrapped_description(text, width=CARD_WIDTH):
    """Print DESCRIPTION and wrap text so whole words move to the next line."""
    label = "DESCRIPTION: "
    wrapper = textwrap.TextWrapper(
        width=width,
        initial_indent=label,           # first line starts with the label
        subsequent_indent=" " * len(label),  # extra lines line up under the text
        break_long_words=True,          # only if one word is longer than the line
        break_on_hyphens=True,          # may break after a hyphen already in the word
    )
    print(wrapper.fill(text))

# 1b. Clear the terminal screen
def clear_screen(margin=True):
    """Erase the terminal, then leave a little space at the top."""
    os.system('cls' if os.name == 'nt' else 'clear')    
    if margin:
        print("\n" * TOP_MARGIN)        # leave a little space at the top of the screen

# 1c. Print a banner for the choices
def print_mode_banner(title):
    """Print a banner for the mode the user has chosen."""
    print("=" * CARD_WIDTH)
    print(f" {title} ".center(CARD_WIDTH, "="))
    print("=" * CARD_WIDTH)

# 1d. Clear the hint line
def overwrite_line(text):
    """Print text, stay on the line, then erase it after the keypress."""
    print(text, end="", flush=True)
    action = read_enter_or_esc()
    print("\r" + " " * len(text) + "\r", end="", flush=True)
    return action

# 1e. Enter to continue or Esc to go back to menu
def read_enter_or_esc():
    """
    Wait for one key.
    Returns 'enter' or 'esc'.
    Other keys are ignored.
    """
    try:
        import msvcrt   # Windows
        while True:
            ch = msvcrt.getwch()
            if ch in ("\r", "\n"):
                return "enter"
            if ch == '\x1b':            # ESC
                return "esc"
            # arrow keys send a prefix + a second code; skip the extra
            if ch in ("\x00", "\xe0"):
                msvcrt.getwch()
    except ImportError:
        import sys, tty, termios        # macOS / Linux
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            while True:
                ch = sys.stdin.read(1)
                if ch in ("\r", "\n"):
                    return "enter"
                if ch == "\x1b":
                    return "esc"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)

# 1f. Open scripts from an entered directory
def script_folder():
    """Return the folder where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

# 1g. Open csv's from the data folder
def csv_path(filename):
    """Return the full path to a CSV file in the data folder under this program's directory."""
    return os.path.join(script_folder(), DATA_FOLDER, filename)


# 1h. Turn what the user typed into a full path to a CSV file
def resolve_csv_path(name):
    """Turn what the user typed into a full path to a CSV"""
    name = name.strip().strip('"')                  # Remove whitespace and quotes
    if not name.lower().endswith(".csv"):
        name = name + ".csv"
    if os.path.isabs(name):
        return name
    return csv_path(name)


# 2. Load the flashcards from CSV
def load_flashcards(filename, deck_label=None):
    """Load one CSV. Each card remembers which deck it came from."""
    path = filename if os.path.isabs(filename) else csv_path(filename)
    if deck_label is None:
        deck_label = os.path.splitext(os.path.basename(path))[0] # Use filename without extension as default label

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
def lookup_acronym(flashcards):
    """Find a card with this acronym in the loaded deck(s)."""
    while True:
        query = input("Enter the acronym to lookup (blank = menu): ").strip()
        if not query:
            return
    
        query_upper = query.upper()
        matches = [
        card for card in flashcards
        if card["acronym"].strip().upper() == query_upper
        ]

        if not matches:
            print(f'No card found for "{query}".')
            print()
            continue

        print(f"Found {len(matches)} card(s) for {query_upper}.")
        for number, card in enumerate(matches, start=1):
            print(f"\nMatch {number} of {len(matches)}")
            show_full_card(card)
        print()


# 4. Show a single flashcard with the option to reveal or go back to menu
def show_card(card, number=None, total=None):
    """ Show one flashcard, reveal on Enter, or go back to menu on Esc."""
    print("\n" + "=" * CARD_WIDTH)
    if number is not None and total is not None:
        print(f"Card {number} of {total}")
    print(f"ACRONYM:     {card['acronym']}")
    print(f"DECK:        {card.get('deck', '')}")
    if overwrite_line("ENTER = reveal     ESC = menu") == "esc":
        return "esc"
    
    print(f"FULL NAME:   {card['full_name']}")
    print_wrapped_description(card["description"])
    print("=" * CARD_WIDTH)

    return overwrite_line("ENTER = next card     ESC = menu")


# 5. Show a full single flashcard without options
def show_full_card(card):
    """Show every field at once. No Enter/Esc options."""
    print("\n" + "=" * CARD_WIDTH)
    print(f"ACRONYM:     {card['acronym']}")
    print(f"DECK:        {card.get('deck', '')}")
    print(f"FULL NAME:   {card['full_name']}")
    print_wrapped_description(card["description"])
    print("=" * CARD_WIDTH)
    input("Press ENTER to continue...")


# 6. Flashcard deck chooser
def choose_deck():
    """Let the user choose a built-in deck or load all."""

    all_num = len(BUILTIN_DECKS) + 1
    own_num = len(BUILTIN_DECKS) + 2

    while True:
        clear_screen()
        print("Which deck do you want to study?\n")

        for number, (label, filename) in enumerate(BUILTIN_DECKS, start=1):
            exists = " " if os.path.exists(csv_path(filename)) else " (file not found yet)"
            print(f"{number}. {label}{exists}")

        print(f"{all_num}. All built-in decks")
        print(f"{own_num}. My own CSV file")
        print("0. Exit")


        raw = input("\nEnter a number: ").strip()
        if raw == "0":
            return None, None
        if not raw.isdigit():
            print("Please type a number.")
            input("Press ENTER to continue...")
            continue

        choice = int(raw)

        if 1 <= choice <= len(BUILTIN_DECKS):
            label, filename = BUILTIN_DECKS[choice - 1]
            if not os.path.exists(csv_path(filename)):
                print(f"Create {filename} in the {DATA_FOLDER} folder first.")
                input("Press ENTER to continue...")
                continue
            return label, load_flashcards(filename, label)

        if choice == all_num:
            cards, missing = load_all_builtin()
            if missing:
                print("Skipped missing files:", ", ".join(missing))
                input("Press ENTER to continue...")
            if not cards:
                print("No decks found yet.")
                input("Press ENTER to continue...")
                continue
            return "ALL DECKS", cards

        if choice == own_num:
            print(f"\nType a deck name from the {DATA_FOLDER} folder (.csv is added for you),")
            print("or a full path such as C:\\Decks\\mine.csv")
            name = input("Deckname or Full Pathname: ")
            if not name.strip():
                continue
            path = resolve_csv_path(name)
            if not os.path.exists(path):
                print(f"File not found: {path}")
                input("Press ENTER to continue...")
                continue
            deck_label = os.path.basename(path)
            return deck_label, load_flashcards(path, deck_label)

        print("That number is not on the list.")
        input("Press ENTER to continue...")


# 7. 
def say_goodbye():
    """Print the exit message."""
    print()
    print("Thank you for using the Acronym Finder Flashcards program! Goodbye! 👋")
    print("Made with 💭 by TristanTango73")
    print("\n\n")



# 8. Main program loop
def main():
    while True:             # deck loop
        deck_name, flashcards = choose_deck()
        if deck_name is None:                                       # user chose exit 
            say_goodbye()
            return
        if not flashcards:
            print("That deck has no cards yet.")
            input("Press ENTER to continue...")
            continue

        while True:                                                    # mode loop for this deck
            clear_screen()
            print(f"Deck: {deck_name}")
            print(f"Loaded {len(flashcards)} flashcards! 🎉\n")
            print("What would you like to do?")
            print("1. Review all cards in order")
            print("2. Random quiz mode")
            print("3. Look up a specific acronym")
            print("4. Choose a different deck")
            print("5. Exit")
            print()

            choice = input("Enter 1, 2, 3, 4, or 5: ").strip()

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
                clear_screen(margin=False)
                print_mode_banner("LOOKUP")
                print()
                lookup_acronym(flashcards)
                

            elif choice == "4":
                break                                               # back to the deck loop

            elif choice == "5":
                say_goodbye()
                return                                          # leave main() entirely

            else:
                print("Invalid choice, please try again.")
                input("Press ENTER to continue...")

# This runs the program when you type: py flashcards.py
if __name__ == "__main__":
    main()