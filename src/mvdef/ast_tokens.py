from asttokens import ASTTokens
from ast import Import as IType, ImportFrom as IFType, FunctionDef, walk

__all__ = ["get_tokenised", "get_tree", "get_imports", "get_defs", "locate_import_ends"]

def get_tokenised(filepath):
    with open(filepath, "r") as f:
        source = f.read()
    tokenised = ASTTokens(source, parse=True)
    return tokenised


def get_tree(filepath):
    tree = get_tokenised(filepath).tree
    return tree


def get_imports(tr, index_list=None, trunk_only=True):
    """
    Using the `asttoken`-tokenised AST tree body ("trunk"), get the
    top-level import statements. Alternatively, get imports at any
    level by walking the full tree rather than just the trunk.
    """
    if trunk_only:
        imports = [t for t in tr if type(t) in (IType, IFType)]
    else:
        imports = [t for t in walk(tr) if type(t) in (IType, IFType)]
    if index_list is not None:
        for (n, n_i) in index_list:
            return [imports[i] for i in index_list]
    return imports


def get_defs(tr, def_list=[], trunk_only=True):
    """
    Using the `asttoken`-tokenised AST tree body ("trunk"), get the top-level
    function definition statements. Alternatively, get function definitions
    at any level by walking the full tree rather than just the trunk.
    """
    if trunk_only:
        defs = [t for t in tr if type(t) is FunctionDef]
    else:
        defs = [t for t in walk(tr) if type(t) is FunctionDef]
    if def_list == []:
        return defs
    else:
        return [d for d in defs if d.name in def_list]


def locate_import_ends(source_filepath, index_list=None):
    ends = []
    nodes = get_imports(source_filepath, index_list)
    for n in nodes:
        end = {}
        end["line"], end["index"] = n.last_token.end[0]
        ends.append(end)
    return ends
