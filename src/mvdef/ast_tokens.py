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


def get_defs_and_classes(tr, trunk_only=True):
    """
    List the funcdefs and classdefs of the AST top-level trunk (`tr`), walking it if
    `trunk_only` is `False` (default: `True`), else just list top-level `trunk` nodes.
    """
    defs = [t for t in (tr if trunk_only else walk(tr)) if type(t) is FunctionDef]
    classes = [t for t in (tr if trunk_only else walk(tr)) if type(t) is ClassDef]
    return defs, classes

### Helper functions used for finding the node given a path within `set_defs_to_move`
def _name_check(node, name):
    return node.name == name

def _find_node(nodes, name):
    p_name_check = partial(_name_check, name=name)
    return next(filter(p_name_check, nodes))

def _find_def(node, name):
    def_nodes = [n for n in node.body if type(n) is FunctionDef]
    return _find_node(def_nodes, name)

def set_defs_to_move(src, dst, trunk_only=True):
    """
    Using the `asttoken`-tokenised AST tree body ("trunk"), get the top-level
    function definition statements. Alternatively, get function definitions
    at any level by walking the full tree rather than just the trunk.
    """
    def_list = src.mvdefs
    into_list = src.into_paths
    src_defs, src_classes = get_defs_and_classes(src.trunk, trunk_only=trunk_only)
    dst_defs, dst_classes = get_defs_and_classes(dst.trunk, trunk_only=trunk_only)
    if any(sep in x for sep in [*":."] for x in def_list):
        target_defs = []
        for s, to in zip(def_list, into_list):
            path_parsed = FuncDefPathString(s)
            into_path_parsed = FuncDefPathString(to if to else "")
            if to:
                # Cannot use `check_against_linkedfile` without type of root node
                into_path_root, *into_path_rest = into_path_parsed.parts
                if into_path_rest:
                    # More than 1 part therefore can detect root node type from sep
                    i_root_type = into_path_root.part_type
                    if i_root_type == "Func":
                        into_path_subtyped = FuncDefPathString(to)
                    elif i_root_type == "Class":
                        into_path_subtyped = ClassDefPathString(to)
                    else:
                        raise NotImplementedError(f"Invalid path root: {to}")
                else:
                    # Cannot detect, must check dst_defs and dst_classes
                    any_def = any(into_path_root == f.name for f in dst_defs)
                    any_cls = any(into_path_root == c.name for c in dst_classes)
                    if any_def:
                        breakpoint()
                        raise NotImplementedError("Need to write FuncPath(FuncDefPathString) in ast_util")
                    elif any_cls:
                        raise NotImplementedError("Need to write ClassPath(ClassDefPathString) in ast_util")
                    else:
                        breakpoint()
                        raise NotImplementedError("Too ambiguous to detect")
                into_path_parsed.node = into_path_subtyped.check_against_linkedfile(dst)
            else:
                into_path_parsed.node = to # propagate None
            # handle into_path_parsed.parts[0].part_type, if Func then inner func etc
            if not path_parsed.is_supported_path:
                supported = "inner funcdefs and methods of global-scope classes"
                raise NotImplementedError(f"Currently only supporting {supported}")
            elif not path_parsed.is_inner_func_path_only:
                def_list_path = MethodDefPathString(s)
                c_name = def_list_path.global_cls_name
                # inner funcdefs went here
                initial_cls = _find_node(src_classes, c_name)
                fd = reduce(_find_def, def_list_path.parts[1:], initial_cls)
                fd.path = path_parsed
                fd.into_path = into_path_parsed
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
                initial_def = _find_node(src_defs, f_name)
                fd = reduce(_find_def, def_list_path.parts[1:], initial_def)
                fd.path = path_parsed
                fd.into_path = into_path_parsed
                target_defs.append(fd)
        # To be consistent with the trivial case below, the defs must remain in
        # the same order they appeared in the AST, i.e. in ascending line order
        target_defs = sorted(target_defs, key=lambda d: d.lineno)
    else:
        # Only trivial single part path(s), i.e. global-scope funcdef name(s)
        target_defs = [fd for fd in src_defs if fd.name in def_list]
        for fd in target_defs:
            to = into_list[def_list.index(fd.name)]
            path_parsed = FuncDefPathString(fd.name)
            into_path_parsed = FuncDefPathString(to if to else "")
            fd.path = path_parsed
            fd.into_path = into_path_parsed
    src.defs_to_move = target_defs


def locate_import_ends(source_filepath, index_list=None):
    ends = []
    nodes = get_imports(source_filepath, index_list)
    for n in nodes:
        end = {}
        end["line"], end["index"] = n.last_token.end[0]
        ends.append(end)
    return ends
