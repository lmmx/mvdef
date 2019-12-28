from os import linesep as nl


def terminal_whitespace(inputfile, from_file=True):
    """
    Return the number of whitespace newlines in the file.

    If the file contains no newlines, returns 0.
    """
    if from_file:
        with open(inputfile, "r") as f:
            lines = f.readlines()
    else:
        lines = inputfile
    terminal_i = -1
    for i, line in enumerate(reversed(lines)):
        if line.rstrip(nl) == "":
            if i - terminal_i > 1:
                break
            else:
                # Accumulate consecutive whitespace index until returning
                terminal_i = i
    return terminal_i + 1
