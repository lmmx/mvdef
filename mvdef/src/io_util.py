from os import linesep

def terminal_whitespace(filepath):
    """
    Return the number of whitespace newlines in the file.

    If the file contains no newlines, returns 0.
    """
    terminal_i = -1
    with open(filepath, "r") as f:
        for i, line in enumerate(reversed(f.readlines())):
            if line.rstrip(linesep) == "":
                if i - terminal_i > 1:
                    break
                else:
                    # Accumulate consecutive whitespace index until returning
                    terminal_i = i
    return terminal_i + 1
