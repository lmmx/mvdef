from asttokens import ASTTokens
from ast import Import as IType, ImportFrom as IFType, ClassDef, FunctionDef, walk
from .def_path_util import FuncDefPathString, InnerFuncDefPathString, MethodDefPathString
from functools import reduce, partial

__all__ = ["get_tokenised", "get_tree", "get_imports", "set_defs_to_move", "locate_import_ends"]


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


def set_defs_to_move(src, trunk_only=True):
    """
    Using the `asttoken`-tokenised AST tree body ("trunk"), get the top-level
    function definition statements. Alternatively, get function definitions
    at any level by walking the full tree rather than just the trunk.
    """
    tr = src.trunk
    def_list = src.mvdefs
    into_list = src.into_paths
    defs = [t for t in (tr if trunk_only else walk(tr)) if type(t) is FunctionDef]
    classes = [t for t in (tr if trunk_only else walk(tr)) if type(t) is ClassDef]
    if any(sep in x for sep in [*":.@"] for x in def_list):
        ### Some inner functions used for finding the node given a path
        def name_check(node, name):
            return node.name == name
        def find_node(nodes, name):
            p_name_check = partial(name_check, name=name)
            return next(filter(p_name_check, nodes))
        def find_def(node, name):
            def_nodes = [n for n in node.body if type(n) is FunctionDef]
            return find_node(def_nodes, name)
        ###
        target_defs = []
        for s, to in zip(def_list, into_list):
            path_parsed = FuncDefPathString(s)
            into_path_parsed = FuncDefPathString(to if to else "")
            # handle into_path_parsed.parts[0].part_type, if Func then inner func etc
            toks = path_parsed._tokens
            if any(
                t.name not in ("InnerFunc", "Method")
                for t in path_parsed._tokens
                if type(t) is FuncDefPathString.PathSepEnum
            ):
                supported = "inner funcdefs and methods of global-scope classes"
                raise NotImplementedError(f"Currently only supporting {supported}")
            elif any(
                t.name != "InnerFunc"
                for t in path_parsed._tokens
                if type(t) is FuncDefPathString.PathSepEnum
            ):
                def_list_path = MethodDefPathString(s)
                c_name = def_list_path.global_cls_name
                # inner funcdefs went here
                initial_cls = find_node(classes, c_name)
                fd = reduce(find_def, def_list_path.parts[1:], initial_cls)
                target_defs.append(fd)
                if len(def_list_path.parts[1:]) == 1:
                    parent_cls = initial_cls
                    #fd.parent_cls = parent_cls
                    fd.has_siblings = any(x for x in parent_cls.body if x is not fd)
                else:
                    # store parent if inner class, then check it for other siblings
                    raise NotImplementedError("TODO: store parent if it's inner class")
            else:
                def_list_path = InnerFuncDefPathString(s)
                f_name = def_list_path.global_def_name
                # inner funcdefs went here
                initial_def = find_node(defs, f_name)
                fd = reduce(find_def, def_list_path.parts[1:], initial_def)
                target_defs.append(fd)
        # To be consistent with the trivial case below, the defs must remain in
        # the same order they appeared in the AST, i.e. in ascending line order
        target_defs = sorted(target_defs, key=lambda d: d.lineno)
    else:
        # Only trivial single part path(s), i.e. global-scope funcdef name(s)
        target_defs = [d for d in defs if d.name in def_list]
    src.defs_to_move = target_defs


def locate_import_ends(source_filepath, index_list=None):
    ends = []
    nodes = get_imports(source_filepath, index_list)
    for n in nodes:
        end = {}
        end["line"], end["index"] = n.last_token.end[0]
        ends.append(end)
    return ends
