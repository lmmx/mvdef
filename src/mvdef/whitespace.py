from .log_utils import set_up_logging

__all__ = ["normalise_whitespace"]

logger = set_up_logging(__name__)


def normalise_whitespace(lines: list[str | None], spacing: int = 2) -> str:
    """
    Add more surrounding whitespace by replacing a None with one or more newlines.
    or remove surrounding whitespace by replacing a newline with a None.

    Always prefer to change the None to 1 or 2 newlines rather than prepend to a line.

    >>> ["\n", None, "\n", "x"]     # (start) +2 -> [None, None, None, "x"]
    >>> ["x", "\n", None, "\n"]     #   (end) +2 -> ["x", None, None, None]
    >>> ["x", "\n", None, "\n", "x"]        #  0
    >>> ["x", "\n", None, "x"]              # -1  -> ["x", "\n", "\n", "x"]
    >>> ["x", "\n", "\n", None, "\n", "x"]  # +1  -> ["x", "\n", None, None, "\n", "x"]

    Most you ever have to look is 3 before or after. If this range is shorter, it's at a
    file terminus (so keep ranges separate to know which one).

    Real file may not be ideal (Black format) though, so keep getting newlines if can't
    assume 2. In which case, consider a 2nd newline as "2nd or more".

    Algorithmically: count all newlines immediately surrounding each None (consecutive or
    only separated by other None) and 'squeeze' or 'expand' to the appropriate count:
    - squeeze if sum > 2, replace
      - all but 2 with None if not at terminus
      - all with None if at terminus
    - expand if sum < 2, replace None with
      - 1 newline if count is 1
      - 2 newlines if count is 0
    """
    nones_idx = [i for i, x in enumerate(lines) if x is None]
    nl_idx = [i for i, x in enumerate(lines) if x == "\n"]
    non_text_idx = sorted([*nones_idx, *nl_idx])
    line_count = len(lines)
    last_idx = line_count - 1
    # If you only have None and newlines at either terminus, nullify them all
    # replaced with listcomp:
    first_text_idx = next((i for i in range(line_count) if i not in non_text_idx), 0)
    head_whitespace = [nl_i for nl_i in nl_idx if nl_i < first_text_idx]
    last_text_idx = next(
        (i for i in range(line_count - 1, -1, -1) if i not in non_text_idx), last_idx
    )
    tail_whitespace = [nl_i for nl_i in nl_idx if nl_i > last_text_idx]
    term_ws_idx = sorted(set([*head_whitespace, *tail_whitespace]))
    # Replace terminal newlines with None, deleting them from the result
    pruned_lines = [x if i not in term_ws_idx else None for i, x in enumerate(lines)]
    # Squeeze any remaining 'newline islands' between first_text_idx and last_text_idx
    prev_text_idx = first_text_idx
    next_text_idx_gen = (
        i + 1
        for i in non_text_idx
        if i + 1 not in non_text_idx
        if i + 1 <= last_text_idx
        if i + 1 > prev_text_idx
    )
    logger.debug(non_text_idx)
    for next_text_idx in next_text_idx_gen:
        # Use the prev_text_idx value then 'step along' by overwriting it
        logger.debug(f"{prev_text_idx}::{next_text_idx}")
        island_range = range(prev_text_idx + 1, next_text_idx)
        # We only care about the islands surrounding Nones (where mvdef has operated)
        island_nones_idx = [i for i in nones_idx if i in island_range]
        if island_nones_idx:
            island_nl_idx = [i for i in nl_idx if i in island_range]
            nl_deficit = spacing - len(island_nl_idx)
            debug_msg = (
                f"  ({pruned_lines[prev_text_idx]}) "
                f"{[pruned_lines[i] for i in island_range]} "
                f"({pruned_lines[next_text_idx]})\n"
                f"  nl -> {island_nl_idx}\n"
                f"  {nl_deficit=}"
            )
            logger.debug(debug_msg)
            if nl_deficit > 0:
                # Expand as many Nones as needed by duplicating into a list of newlines
                first_available_none_idx = island_nones_idx[0]
                pruned_lines[first_available_none_idx] = ["\n"] * nl_deficit
            elif nl_deficit < 0:
                # Squeeze as many newlines as needed by replacing with (scalar) None
                easing_idxs = island_nl_idx[:-nl_deficit]
                for nl_idx in easing_idxs:
                    pruned_lines[nl_idx] = None
        prev_text_idx = next_text_idx
    result = [
        ln
        for sublist in pruned_lines
        for ln in (sublist if isinstance(sublist, list) else [sublist])
        if ln is not None
    ]
    return "".join(result)
