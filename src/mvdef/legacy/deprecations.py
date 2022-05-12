from sys import stderr

__all__ = ["pprint_def_names"]


def pprint_def_names(def_names, no_funcdef_list=False):
    if no_funcdef_list:
        print("  {", file=stderr)
        for m in def_names:
            print(f"    {m}: {def_names.get(m)}", file=stderr)
        print("  }", file=stderr)
    else:
        for n in def_names:
            print(f"  {n}:::" + "{", file=stderr)
            for m in def_names.get(n):
                print(f"    {m}: {def_names.get(n)[m]}", file=stderr)
            print("  }", file=stderr)
    return
