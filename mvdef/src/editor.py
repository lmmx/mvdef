from src.ast_tokens import get_imports, count_imported_names, locate_import_ends


def transfer_mvdefs(src_path, dst_path, imports, mvdefs, src_agenda, dst_agenda):
    # ------------------------- First move the imports ------------------------------
    # Do not need to handle "copy", "keep", or "stay" edit_agenda entries,
    # "copy" entries in src_agenda are mirrored by "echo" entries in dst_agenda
    for rm_i in dst_agenda.get("lose"):
        # Remove rm_i (imported name marked "lose") from the source file
        pass
    for mv_i in dst_agenda.get("take"):
        # Transfer mv_i into the destination file: receive "move" as "take"
        pass
    for cp_i in dst_agenda.get("echo"):
        # Transfer cp_i into the destination file: receive "copy" as "echo"
        pass
    for mvdef in mvdefs:
        # Transfer mvdef into the destination file: receive mvdef
        pass
    # -------- Line number preservation no longer needed, only now modify src -------
    for mvdef in mvdefs:
        # Remove mvdef (function def. marked "mvdef") from the source file
        pass
    for mv_i in src_agenda.get("move"):
        # Remove mv_i (imported name marked "move") from the source file
        pass
    for rm_i in src_agenda.get("lose"):
        # Remove rm_i (imported name marked "lose") from the source file
        pass
    return
