from asttokens import ASTTokens
from ast import Import as IType, ImportFrom as IFType, FunctionDef, walk
from .def_path_util import FuncDefPathString, InnerFuncDefPathString
from functools import reduce, partial

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
    defs = [t for t in (tr if trunk_only else walk(tr)) if type(t) is FunctionDef]
    if def_list == []:
        return defs
    else:
        if any(sep in x for sep in [*":.@"] for x in def_list):
            defs_to_move = []
            for s in def_list:
                path_parsed = FuncDefPathString(s)
                toks = path_parsed._tokens
                if any(
                    t.name != "InnerFunc"
                    for t in path_parsed._tokens
                    if type(t) is FuncDefPathString.PathSepEnum
                ):
                    raise NotImplementedError("Currently only supporting inner funcdefs")
                else:
                    def_list_path = InnerFuncDefPathString(s)
                    f_name = def_list_path.global_def_name
                    def name_check(node, name):
                        return node.name == name
                    def find_node(nodes, name):
                        p_name_check = partial(name_check, name=name)
                        return next(filter(p_name_check, nodes))
                    def find_subnode(node, name):
                        def_nodes = [n for n in node.body if type(n) is FunctionDef]
                        return find_node(def_nodes, name)
                    initial_def = find_node(defs, f_name)
                    fd = reduce(find_subnode, def_list_path.parts[1:], initial_def)
                    defs_to_move.append(fd)
            # To be consistent with the trivial case below, the defs must remain in
            # the same order they appeared in the AST, i.e. in ascending line order
            defs_to_move = sorted(defs_to_move, key=lambda d: d.lineno)
            return defs_to_move
        else:
            # Only trivial single part path(s), i.e. global-scope funcdef name(s)
            return [d for d in defs if d.name in def_list]


def locate_import_ends(source_filepath, index_list=None):
    ends = []
    nodes = get_imports(source_filepath, index_list)
    for n in nodes:
        end = {}
        end["line"], end["index"] = n.last_token.end[0]
        ends.append(end)
    return ends
