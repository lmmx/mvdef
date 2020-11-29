from .colours import colour_str as colour

__all__ = ["pprint_agenda_desc", "pprint_agenda", "describe_def_name_dict"]

def pprint_agenda_desc(category, entry_key, entry_dict, extra_message=""):
    """
    Pretty print an edit agenda entry according to the agenda category.
    The 7 categories are: move, keep, copy, lose, take, echo, stay.
    """
    entry_desc = describe_def_name_dict(entry_key, entry_dict)
    if category == "move":
        m = colour("green", f" ⇢ MOVE  ⇢ {entry_desc}" + extra_message)
    elif category == "keep":
        m = colour("dark_gray", f"⇠  KEEP ⇠  {entry_desc}" + extra_message)
    elif category == "copy":
        m = colour("light_blue", f"⇠⇢ COPY ⇠⇢ {entry_desc}" + extra_message)
    elif category == "lose":
        m = colour("red", f" ✘ LOSE ✘  {entry_desc}" + extra_message)
    elif category == "take":
        m = colour("green", f" ⇢ TAKE  ⇢ {entry_desc}" + extra_message)
    elif category == "echo":
        m = colour("light_blue", f"⇠⇢ ECHO ⇠⇢ {entry_desc}" + extra_message)
    elif category == "stay":
        m = colour("dark_gray", f"⇠  STAY ⇠  {entry_desc}" + extra_message)
    else:
        raise ValueError(f"Unknown agenda category: {category}")
    print(m)
    return


def pprint_agenda(agenda):
    for category in agenda:
        for entry in agenda.get(category):
            name, info_dict = list(entry.items())[0]
            pprint_agenda_desc(category, name, info_dict)
    return


def describe_def_name_dict(name, name_dict):
    """
    Wrapper function that returns a string presenting the content of a dict entry
    with import statement indexes, line number, and import source path. These
    fields are instantiated within `get_def_names`, which in turn is assigned to
    the variable `mvdef_names` within `parse_mv_funcs`.
    
    The output of `parse_mv_funcs` gets passed to `process_ast`, which iterates over
    the subsets within the output of `parse_mv_funcs`, at which stage it's
    necessary to produce a nice readable output, calling `describe_mvdef_name_dict`.
    """
    # Extract: import index; intra-import index; line number; import source
    n, n_i, ln, imp_src = [name_dict.get(x) for x in ["n", "n_i", "line", "import"]]
    desc = f"(import {n}:{n_i} on line {ln}) {name} ⇒ <{imp_src}>"
    return desc
