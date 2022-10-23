# flake8: noqa
from os import linesep as nl

from .io_util import terminal_whitespace

__all__ = [
    "get_defrange",
    "get_defstring",
    "append_def_to_file",
    "get_def_lines",
    "excise_def_from_file",
    "excise_def_lines",
    "get_borders",
    "overwrite_import",
]


def get_defrange(def_node):
    """
    def_node:    An ast.FunctionDefinition node with start/end position annotations
                 from the asttokens library.
    """
    def_startline = def_node.first_token.start[0] - 1  # Subtract 1 to get 0-base index
    def_endline = def_node.last_token.end[0]  # Don't subtract 1, to include full range
    defrange = [def_startline, def_endline]
    return defrange


def get_defstring(def_node, file_lines):
    """
    def_node:    An ast.FunctionDefinition node with start/end position annotations
                 from the asttokens library.
    file_lines:  A list from readlines (should contain the appropriate file system
                 newlines, the list will be joined with a blank string).
    """
    def_startline, def_endline = get_defrange(def_node)
    deflines = file_lines[def_startline:def_endline]
    defstring = "".join(deflines)
    return defstring


def append_def_to_file(defstring, dst_path):
    """
    Insert the lines of a function defintion into a file (in future this function may
    permit insertion at a certain order position in the file's function definitions).

    `defstring` must be a string containing appropriate newlines for a Python file.
    """
    # Assess the whitespace, leave at least 2
    end_blanklines = terminal_whitespace(dst_path)
    append_newlines = max((0, 2 - end_blanklines)) * nl
    with open(dst_path, "a") as f:
        f.write(append_newlines + defstring)
    return


def get_def_lines(deflines, dst_lines, is_inner=False, indent_delta=0):
    """
    Get the list of lines of a func. def. suitable to be appended to a set of lines.

    `deflines` must be a list of strings containing appropriate newlines for a Python
    file (the lines will not be joined with newlines, they must be already supplied).
    """
    # Assess the whitespace, leave at least 2 if outer, 1 if inner
    window_size = 1 if is_inner else 2
    end_blanklines = terminal_whitespace(dst_lines, from_file=False)
    append_newlines = [nl for _ in range(max((0, window_size - end_blanklines)))]
    if indent_delta > 0:
        # Indent
        indent = " " * indent_delta
        deflines = [f"{indent}{l}" for l in deflines]
    elif indent_delta < 0:
        # Deindent
        deindent = abs(indent_delta)
        deflines = [l[deindent:] for l in deflines]
    return append_newlines + deflines


def excise_def_from_file(def_node, py_path, return_def=True):
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
        # Inkeeping with convention, range is inclusive at start, exclusive at end i.e. [)
        def_startline = def_node.first_token.start[0] - 1
        def_endline = def_node.last_token.end[0]
        defrange = [def_startline, def_endline]
        pre = (def_startline - 2, def_startline)
        post = (def_endline, def_endline + 2)
        # Count whitespace above and below the function definition
        wspace_a = [x == nl for x in lines[pre[0] : pre[1]]]
        wspace_b = [x == nl for x in lines[post[0] : post[1]]]
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
            del excised_lines[i]  # Delete lines backwards from end of file line range
    if return_def:
        deflines = lines[def_startline:def_endline]
        return deflines
    else:
        # Edit file in place (N.B. will not use this actually)
        return


def excise_def_lines(def_node, lines):
    """
    Delete a function definition using its AST node (via asttokens) from a list of lines
    which originated from a single, entire, Python file.

    If the deleted function was the only element in the body of its parent, then replace
    it with a `pass` statement to ensure the file remains valid.

    Ensure 2 lines between global-level nodes, and 1 line between inner nodes.
    """
    window_size = 2  # used in get_borders
    inner_window_size = 1  # used in repairing method-excised empty classdefs
    def_startline = def_node.first_token.start[0]
    def_endline = def_node.last_token.end[0]
    # Subtract 1 from start line index for 0-based "inclusive start/exclusive end"
    defrange = [def_startline - 1, def_endline]
    pre, post = get_borders(defrange, lines, window_size=window_size)
    # Count whitespace above and below the function definition
    # Reverse the order of `pre` otherwise redefining the range start to be the 1st
    # would also necessarily include the 2nd elem of `pre` within the range
    wspace_pre = [lines[p] == nl for p in pre[::-1]]
    wspace_post = [lines[p] == nl for p in post]
    wspace_count = (wspace_pre + wspace_post).count(True)
    if wspace_count > window_size:
        # Remove whitespace: get list of indexes of lines which are blank
        # Reverse pre so as to match the index of `wspace_pre` as above
        pp = pre[::-1] + post
        ws_li = [pp[i] for (i, x) in enumerate((wspace_pre + wspace_post)) if x]
        # Take as many as reduce the whitespace count to window size (2)
        remove_li = [ws_li[n] for n in range(wspace_count - window_size)]
        for li in remove_li:
            # Reduce whitespace border by extending defrange to include it
            if li < min(defrange):
                defrange[0] = li
            elif li > max(defrange):
                defrange[1] = li
            # Otherwise li is intermediate (already processed a past li, continue)
    # Whitespace count of less than 2 could only happen when a def is at the end of
    # a file, in which case no need to add whitespace, so no need to check for it.
    if hasattr(def_node, "has_siblings") and not def_node.has_siblings:
        repair_lines = [f"{' ' * def_node.col_offset}pass"]
        repair_lines.extend([""] * inner_window_size)  # leave the window of 1 line
    else:
        repair_lines = []
    for i, r in enumerate(range(*defrange)):
        if i < len(repair_lines):
            # print(f"Replacing '{lines[r]}' with '{repair_lines[i]}'")
            lines[r] = repair_lines[i]
        else:
            # print(f"Deleting '{lines[r]}'")
            lines[r] = None  # Mark lines as deleted by setting the string to `None`
    return


def get_borders(defrange, lines, window_size=2):
    """
    Given the range corresponding to a function definition, and the list of lines
    this range is in reference to, and the "window size" of the number of lines
    to compare on each [out]side of this range, return the list of indices of
    lines which are not `None`.

    This is necessary when some lines have been 'nullified' by replacing the string
    at that index with `None`, so as to conserve the line numbering while removing
    lines (i.e. after excising import names and/or function definitions).

    The expected value of the range is to follow Python's convention for ranges,
    i.e. "inclusive start, exclusive end" - mathematically written as `[)`.

    Will return two lists of integers which represent the line indexes of the pre-
    and post-function definition non-`None` lines (i.e. the lines above and below,
    ignoring any lines which have previously been removed). If the `window_size`
    of lines above and/or below is not found, the maximum number of lines will be
    given (i.e. returns empty lists if nothing is found above/below the `defrange`).
    """
    d_start, d_end = defrange
    # Get non-`None` line indexes to a max. of `window_size` away from the start
    where_pre = [i for i, l in enumerate(lines[:d_start][::-1]) if l is not None]
    # Reverse list of index offset from d_start back to normal order, get abs. index
    pre = [d_start - 1 - idx for idx in where_pre[:window_size][::-1]]
    where_post = [i for i, l in enumerate(lines[d_end:]) if l is not None]
    post = [d_end + idx for idx in where_post[:window_size]]
    return pre, post


def overwrite_import(imp_node, replacement_str, lines):
    """
    Similar to `excise_def_from_lines`, this function overwrites the line or lines
    which correspond to an import statement (the AST node of which is given as
    `imp_node`), either replacing each line with the equivalent of `replacement_str`
    (the replacement import statement string generated by `get_import_stmt_str`)
    if the replacement is the same number of lines long, or if the number of lines
    has changed, it will not split the lines and simply place the entire replacement
    import statement string in one entry of the `lines` list, and set the "spare"
    entries over the range previously occupied by the import statement to `None`.
    """
    if not replacement_str.endswith(nl):
        replacement_str += nl
    pre_startline = imp_node.first_token.start[0] - 1
    pre_endline = imp_node.last_token.end[0]
    len_pre = pre_endline - pre_startline + 2
    replacement_lines = [f"{r}{nl}" for r in replacement_str.rstrip(nl).split(nl)]
    len_post = len(replacement_lines)
    if len_pre >= len_post:
        # Replace all lines of pre with lines of post, set any remainder to `None`
        for i in range(len_pre):
            if i in range(len_post):
                post_line = replacement_lines[i]
                lines[pre_startline + i] = post_line
            else:
                lines[pre_startline + i] = None
    else:  # len_pre < len_post
        # Set the original line range to `None`, except for the first line of the
        # range which is replaced with the entire replacement string
        for i in range(len_pre):
            if i > 0:
                lines[pre_startline + i] = None
            else:
                lines[pre_startline] = replacement_str
    return
