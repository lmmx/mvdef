# flake8: noqa
from ast import ClassDef, FunctionDef
from ast import Import as IType
from ast import ImportFrom as IFType
from ast import walk
from functools import reduce

from asttokens import ASTTokens

from .ast_util import (
    ClassPath,
    DefPathTypeEnum,
    DefTypeEnum,
    FuncPath,
    InnerClassPath,
    IntraDefPathTypeEnum,
    MethodPath,
    get_base_type_name,
    has_clsdef_base,
)
from .def_helpers import _find_cls, _find_def, _find_node, _name_check
from .def_path_util import (
    FuncDefPathStr,
    InnerFuncDefPathStr,
    MethodDefPathStr,
    NullPathStr,
    UntypedPathStr,
)

__all__ = [
    "get_tokenised",
    "get_tree",
    "get_imports",
    "set_defs_to_move",
    "locate_import_ends",
]


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


## (Some helper functions excised to def_helpers.py, TODO excise more)


def per_path_part_finder(parent_def, path_part, annotate_siblings=True):
    finder = _find_cls if has_clsdef_base(path_part) else _find_def
    sd = finder(parent_def, path_part)
    sd.has_siblings = any(n for n in parent_def.body if n is not sd)
    return sd


def get_to_node(to, into_path, dst_funcs, dst_classes):
    """
    Annotate the parsed `into_path` with a `.node` attribute, which will be used later
    when determining the line to insert the newly moved funcdef at in the `DstFile`.
    """
    if to:
        # Cannot use `check_against_linkedfile` without type of leaf node
        # (since it's only a defined method for typed DefPath classes)
        into_path_root, into_path_leaf = into_path.parts[0], into_path.parts[-1]
        if len(into_path.parts) > 1:
            # More than 1 part therefore can detect leaf node type from sep
            i_root_type = into_path_root.part_type
            i_leaf_type = into_path_leaf.part_type
            if i_leaf_type in DefPathTypeEnum._member_names_:
                i_leaf_defpath_type = DefPathTypeEnum[i_leaf_type].value
            elif i_leaf_type in IntraDefPathTypeEnum._member_names_:
                i_leaf_defpath_type = IntraDefPathTypeEnum[i_leaf_type].value
            else:
                part_types = [p.part_type for p in into_path.parts]
                raise NotImplementedError(f"{to=} has {part_types=}. Leaf unsupported")
            if i_root_type in DefPathTypeEnum._member_names_:
                base_type_name = i_root_type  # either "Func" or "Class"
            else:
                base_type_name = get_base_type_name(i_root_type)
            into_path = i_leaf_defpath_type(to)
            target_defs = dst_classes if base_type_name == "Class" else dst_funcs
            if not target_defs:
                msg = "Trying to check against an empty list will fail"
                helper = f"are you sure this path {to} is correct?"
                raise ValueError(f"{msg} ({helper})")
            into_path.node = into_path.check_against_defs(target_defs)
        else:
            # Cannot detect, must check dst_funcs and dst_classes
            # into_path will be UntypedPathStr so the part will be UntypedPathPart
            # (so access .string rather than the part directly)
            matched_f = [f for f in dst_funcs if into_path_leaf.string == f.name]
            matched_c = [c for c in dst_classes if into_path_leaf.string == c.name]
            matches = [matched_f, matched_c]
            if all(matches):
                raise NameError(f"Ambiguous whether {into_path_leaf=} is a cls/func")
            elif not any(matches):
                raise NameError(f"{into_path_leaf=} is not an extant cls/def name")
            d_root = into_path.parts[0]
            if not isinstance(d_root, str):
                d_root = d_root.string
            initial_def = _find_node(matched_f if matched_f else matched_c, d_root)
            into_path.node = initial_def
    else:
        into_path.node = to  # propagate None
    return into_path  # now annotated with `.node` attribute


def set_defs_to_move(src, dst, trunk_only=True):
    """
    Using the `asttokens`-tokenised AST tree body ("trunk"), get the top-level
    function definition statements. Alternatively, get function definitions
    at any level by walking the full tree rather than just the trunk.
    """
    def_list = src.mvdefs
    into_list = src.into_paths
    get_cls = src.classes_only
    if not trunk_only:
        raise NotImplementedError("Won't work (see src_funcs/classes/_find_node below)")
    src_funcs, src_classes = get_defs_and_classes(src.trunk, trunk_only=trunk_only)
    dst_funcs, dst_classes = get_defs_and_classes(dst.trunk, trunk_only=trunk_only)
    # Note that you may want to set `into_path.node` even if the mvdef is top-level!
    target_defs = []
    for d, to in zip(def_list, into_list):
        path_parsed = UntypedPathStr(d)  # not final: may actually be a ClassDef!
        if path_parsed.is_unsupported:
            supported = "inner funcdefs and methods of global-scope classes"
            raise NotImplementedError(f"Currently only supporting {supported}")
        elif len(path_parsed.parts) == 1:
            path_parsed = ClassPath(d) if get_cls else FuncPath(d)
        into_path_parsed = UntypedPathStr(to) if to else NullPathStr()
        into_path_parsed = get_to_node(to, into_path_parsed, dst_funcs, dst_classes)
        d_root = path_parsed.parts[0]
        if not isinstance(d_root, str):
            d_root = d_root.string
        # -------------- was a try block
        src_defs = src_classes if has_clsdef_base(d_root, intradef=False) else src_funcs
        initial_def = _find_node(src_defs, d_root)
        sd = reduce(per_path_part_finder, path_parsed.parts[1:], initial_def)
        sd.path = path_parsed
        sd.into_path = into_path_parsed
        target_defs.append(sd)
    # To be consistent with the trivial case below, the defs must remain in
    # the same order they appeared in the AST, i.e. in ascending line order
    target_defs = sorted(target_defs, key=lambda d: d.lineno)
    src.defs_to_move = target_defs


def locate_import_ends(source_filepath, index_list=None):
    ends = []
    nodes = get_imports(source_filepath, index_list)
    for n in nodes:
        end = {}
        end["line"], end["index"] = n.last_token.end[0]
        ends.append(end)
    return ends
