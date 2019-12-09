from src.ast_tokens import get_defs, get_imports, get_tree
from src.editor_util import get_defstring, append_def, excise_def

def transfer_mvdefs(src_path, dst_path, mvdefs, src_agenda, dst_agenda):
    # Firstly annotate ASTs with the asttokens library
    with open(src_path, "r") as f: src_lines = f.readlines()
    with open(dst_path, "r") as f: dst_lines = f.readlines()
    src_trunk = get_tree(src_path).body
    dst_trunk = get_tree(dst_path).body
    src_mvdefs = get_defs(tr=src_trunk, def_list=mvdefs, trunk_only=True)
    src_imports = get_imports(src_trunk, trunk_only=True)
    dst_imports = get_imports(dst_trunk, trunk_only=True)
    # ------------------------- First move the imports ------------------------------
    # Do not need to handle "copy", "keep", or "stay" edit_agenda entries,
    # "copy" entries in src_agenda are mirrored by "echo" entries in dst_agenda
    for rm_i in dst_agenda.get("lose"):
        # Remove rm_i (imported name marked "lose") from the source file
        rm_i_name, dst_info = list(rm_i.items())[0]
        pass
    for mv_i in dst_agenda.get("take"):
        # Transfer mv_i into the destination file: receive "move" as "take"
        mv_i_name, dst_info = list(mv_i.items())[0]
        pass
    for cp_i in dst_agenda.get("echo"):
        # Transfer cp_i into the destination file: receive "copy" as "echo"
        cp_i_name, dst_info = list(cp_i.items())[0]
        pass
    for mvdef in src_mvdefs:
        # Transfer mvdef into the destination file: receive mvdef
        # mvdef is an ast.FunctionDefinition node with start/end position annotations
        defstring = get_defstring(mvdef, src_lines)
        append_def(defstring, src_path, dst_path)
    # -------- Line number preservation no longer needed, only now modify src -------
    # Iterate through funcdefs in reverse line number order (i.e. upward from bottom)
    for mvdef in sorted(src_mvdefs, key=lambda d: d.last_token.end[0], reverse=True):
        # Remove mvdef (function def. marked "mvdef") from the source file
        excise_def(def_node=mvdef, py_path=src_path, return_def=False)
    for mv_i in src_agenda.get("move"):
        # Remove mv_i (imported name marked "move") from the source file
        mv_i_name, src_info = list(mv_i.items())[0]
        pass
    for rm_i in src_agenda.get("lose"):
        # Remove rm_i (imported name marked "lose") from the source file
        rm_i_name, src_info = list(rm_i.items())[0]
        pass
    return
