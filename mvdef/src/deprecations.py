import ast
from pathlib import Path
from collections import OrderedDict
import builtins
from src.display import colour_str as colour
from asttokens import ASTTokens
from src.editor import edit_defs


def pprint_def_names(def_names, no_funcdef_list=False):
    if no_funcdef_list:
        print("  {")
        for m in def_names:
            print(f"    {m}: {def_names.get(m)}")
        print("  }")
    else:
        for n in def_names:
            print(f"  {n}:::" + "{")
            for m in def_names.get(n):
                print(f"    {m}: {def_names.get(n)[m]}")
            print("  }")
    return