from asttokens import ASTTokens
from ast import Import as IType, ImportFrom as IFType, ClassDef, FunctionDef, walk
from .def_path_util import FuncDefPathString, InnerFuncDefPathString, MethodDefPathString
from .ast_util import ClassPath, InnerClassPath, FuncPath, MethodPath
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
    Using the `asttokens`-tokenised AST tree body ("trunk"), get the
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
    "Check whether an AST `node`’s `.name` attribute is `name`"
    return node.name == name

def _find_node(nodes, name):
    "Return the first node in `nodes` whose `.name` attribute is `name`"
    p_name_check = partial(_name_check, name=name)
    try:
        return next(filter(p_name_check, nodes))
    except StopIteration:
        return None

def _find_def(node, name):
    """
    Return the first `ast.FunctionDef` subnode in the body of `nodes` whose `.name`
    attribute is `name`
    """
    def_nodes = [n for n in node.body if type(n) is FunctionDef]
    return _find_node(def_nodes, name)

def get_to_node(to, into_path_parsed, dst_defs, dst_classes):
    """
    Annotate the parsed `into_path` with a `.node` attribute, which will be used later
    when determining the line to insert the newly moved funcdef at in the `DstFile`.
    """
    if to:
        # Cannot use `check_against_linkedfile` without type of leaf node
        *into_path_preamble, into_path_leaf = into_path_parsed.parts
        if into_path_preamble:
            # More than 1 part therefore can detect leaf node type from sep
            i_leaf_type = into_path_leaf.part_type
            if i_leaf_type == "Func":
                # TODO: make a FuncPath
                #raise NotImplementedError("Need to write FuncPath(FuncDefPathString) in ast_util")
                into_path_parsed = FuncPath(to)
                into_path_parsed.node = into_path_parsed.check_against_defs(dst_defs)
            elif i_leaf_type == "Class":
                # TODO: make a ClassPath
                #raise NotImplementedError("Need to write ClassPath(ClassDefPathString) in ast_util")
                into_path_parsed = ClassPath(to)
                raise NotImplementedError("Not written the check_against_classes yet")
                into_path_parsed.node = into_path_parsed.check_against_classes(dst_classes)
            elif i_leaf_type == "Method":
                if len(into_path_preamble) > 1:
                    raise NotImplementedError(f"The method path is too deep: {to}")
                into_path_parsed = MethodPath(to)
                into_path_parsed.node = into_path_parsed.check_against_classes(dst_classes)
            elif i_leaf_type == "InnerClass":
                if len(into_path_preamble) > 1:
                    raise NotImplementedError(f"The inner class is too deep: {to}")
                into_path_parsed = InnerClassPath(to)
                into_path_parsed.node = into_path_parsed.check_against_classes(dst_classes)
            else:
                #breakpoint()
                part_types = [p.part_type for p in into_path_parsed.parts]
                raise NotImplementedError(f"{to=} gave {part_types=}")
        else:
            # Cannot detect, must check dst_defs and dst_classes
            matched_def = [f for f in dst_defs if into_path_leaf == f.name]
            matched_cls = [c for c in dst_classes if into_path_leaf == c.name]
            if all([matched_def, matched_cls]):
                raise NameError(f"Ambiguous whether {into_path_leaf} is a cls/def")
            if matched_def:
                d_name = into_path_parsed.parts[0]
                initial_def = _find_node(matched_def, d_name)
                into_path_parsed.node = initial_def
            elif matched_cls:
                c_name = into_path_parsed.parts[0]
                initial_cls = _find_node(matched_cls, c_name)
                into_path_parsed.node = initial_cls
            else:
                raise NameError(f"{into_path_leaf} is not an extant cls/def name")
    else:
        into_path_parsed.node = to # propagate None
    return into_path_parsed # now annotated with `.node` attribute

def set_defs_to_move(src, dst, trunk_only=True):
    """
    Using the `asttokens`-tokenised AST tree body ("trunk"), get the top-level
    function definition statements. Alternatively, get function definitions
    at any level by walking the full tree rather than just the trunk.
    """
    def_list = src.mvdefs
    into_list = src.into_paths
    if not trunk_only:
        raise NotImplementedError("Won't work (see src_defs/classes/_find_node below)")
    src_defs, src_classes = get_defs_and_classes(src.trunk, trunk_only=trunk_only)
    dst_defs, dst_classes = get_defs_and_classes(dst.trunk, trunk_only=trunk_only)
    # Note that you may want to set `into_path.node` even if the mvdef is top-level!
    if any(sep in x for sep in [*":."] for x in def_list):
        target_defs = []
        for s, to in zip(def_list, into_list):
            path_parsed = FuncDefPathString(s) # not final: may actually be a ClassDef!
            #
            #---#---#--- begin handling `into_path` ---#---#---#
            into_path_parsed = FuncDefPathString(to if to else "")
            into_path_parsed = get_to_node(to, into_path_parsed, dst_defs, dst_classes)
            #---#---#--- done handling `into_path` ---#---#---#
            #
            # handle into_path_parsed.parts[0].part_type, if Func then inner func etc
            if not path_parsed.is_supported_path:
                #breakpoint()
                supported = "inner funcdefs and methods of global-scope classes"
                raise NotImplementedError(f"Currently only supporting {supported}")
            if path_parsed.is_inner_func_path_only:
                def_list_path = InnerFuncDefPathString(s)
                f_name = def_list_path.global_def_name
                # inner funcdefs went here
                initial_def = _find_node(src_defs, f_name)
                fd = reduce(_find_def, def_list_path.parts[1:], initial_def)
                fd.path = path_parsed
                fd.into_path = into_path_parsed
                if len(def_list_path.parts[1:]) == 1:
                    parent_def = initial_def
                    fd.has_siblings = any(x for x in parent_def.body if x is not fd)
                else:
                    # store parent if inner class, then check it for other siblings
                    raise NotImplementedError("TODO: store parent if it's inner class")
                target_defs.append(fd)
            else:
                # presume method
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
                    fd.has_siblings = any(x for x in parent_cls.body if x is not fd)
                else:
                    # store parent if inner class, then check it for other siblings
                    raise NotImplementedError("TODO: store parent if it's inner class")
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
            into_path_parsed = get_to_node(to, into_path_parsed, dst_defs, dst_classes)
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
