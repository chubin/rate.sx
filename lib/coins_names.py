"""
Coins codes and names.
"""

import sys
import re
import os
from typing import Dict, List, Tuple


def coin_name(symbol):
    """
    Return full name of the coin ``symbol``
    """

    return COIN_NAMES_DICT.get(symbol, "")


def load_names() -> List[Tuple[str, str]]:
    """Loads names from all files in the specified directory.

    Each entry in the files has the following format:
    NAME Description

    Returns:
        List[Tuple[str, str]]: A list of tuples where each tuple contains
        the NAME and Description from the files.
    """
    directory_path = os.path.join(os.path.dirname(__file__), "../share/coins/names/")
    names_list = []

    # Ensure the directory exists
    if not os.path.exists(directory_path):
        return names_list

    # Iterate over all files in the directory
    for filename in sorted(os.listdir(directory_path)):
        if not filename.startswith("0"):
            continue
        file_path = os.path.join(directory_path, filename)

        # Only process files, skip directories
        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    # Split each line into a name and description
                    parts = re.split(r'\s+', line, maxsplit=1)
                    if len(parts) == 2:
                        names_list.append((parts[0], parts[1]))

    return names_list


def check_names(existing_names: Dict[str, str]) -> None:
    """Reads names from standard input and prints the names
    that are missing in the provided dictionary.

    Args:
        existing_names: A dictionary of existing names, where keys are
                        the names to be checked against.

    Reads:
        Names from standard input, each in a new line.

    Prints:
        Names that are not found in the 'existing_names' dictionary.
    """
    # Capture input from standard input
    input_names = sys.stdin.read().strip().splitlines()

    # Check for names not found in the given dictionary
    missing_names = [name for name in input_names if name not in existing_names]

    # Print the missing names
    for name in missing_names:
        print(name)


COINS_NAMES = load_names()
COIN_NAMES_DICT = dict(COINS_NAMES)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "dumpnames":
        for pair in COINS_NAMES:
            print(f"{pair[0]:8} {pair[1]}")
    elif len(sys.argv) > 1 and sys.argv[1] == "checknames":
        check_names(COIN_NAMES_DICT)
