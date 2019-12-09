from src.io_util import terminal_whitespace
from os import linesep as linesep


def get_defstring(def_node, file_lines):
    """
    def_node:    An ast.FunctionDefinition node with start/end position annotations
                 from the asttokens library.
    file_lines:  A list from readlines (should contain the appropriate file system
                 newlines, the list will be joined with a blank string).
    """
    def_startline = def_node.first_token.start[0] - 1 # Subtract 1 to get 0-base index
    def_endline = def_node.last_token.end[0] # Don't subtract 1, to include full range
    deflines = file_lines[def_startline : def_endline]
    defstring = ''.join(deflines)
    return defstring


def append_def(defstring, dst_path):
    """
    Insert the lines of a function defintion into a file (in future this function may
    permit insertion at a certain order position in the file's function definitions).

    Defstring must be a string containing appropriate newlines for a Python file.
    """
    # Assess the whitespace, leave at least 2
    end_blanklines = terminal_whitespace(dst_path)
    append_newlines = max((0, 2 - end_blanklines)) * linesep
    with open(dst_path, "a") as f:
        f.write(append_newlines + defstring)
    return

def excise_def(def_node, py_path, return_def=True):
    """
    Either cut or delete a function definition using its AST node (via asttokens).

    If `return_def` is True, modify the file at `py_path` to remove the lines from
    `def_node.first_token.start[0]` to `def_node.last_token.end[0]`, and return the
    string read from the lines from `py_path` which contained it (i.e. a "cut" operation).
    
    If `return_def` is False, modify the file at `py_path` to remove the lines that
    contain the function called `def_name`, return `None` (i.e. a delete operation).
    """
    with open(py_path, "w+") as f:
        lines = f.readlines()
        def_startline = def_node.first_token.start[0] - 1 # Subtract 1 to get 0-base index
        def_endline = def_node.last_token.end[0] # Don't subtract 1, to include full range
        defrange = [def_startline, def_endline]
        pre = (def_startline - 2, def_startline)
        post = (def_endline, def_endline + 2)
        # Count whitespace above and below the function definition
        wspace_a = [x == linesep for x in lines[pre[0] : pre[1]]]
        wspace_b = [x == linesep for x in lines[post[0] : post[1]]]
        wspace_count = (wspace_a + wspace_b).count(True)
        # wspace_added = "" # Don't think I actually need to implement this
        if wspace_count > 2:
            # Remove whitespace: get list of indexes of lines which are blank
            prepost = [p for p in range(*pre)] + [p for p in range(*post)]
            ws_li = [prepost[i] for (i, x) in enumerate((ws_a + ws_b)) if x]
            # Take as many as reduce the whitespace count to 2
            remove_li = [ws_li[n] for n in range(wspace_count - 2)]
            for li in remove_li:
                if li < min(defrange):
                    defrange[0] = li
                elif li > max(defrange):
                    defrange[1] = li
                # Otherwise li is intermediate (already processed a past li, continue)
        # Whitespace count of less than 2 could only happen when a def is at the end of
        # a file, in which case no need to add whitespace, so no need to check for it.
        excised_lines = lines.copy()
        for i in reversed(range(*defrange)):
            del excised_lines[i] # Delete lines backwards from end of file line range
    if return_def:
        deflines = lines[def_startline : def_endline]
        return deflines
    else:
        return
