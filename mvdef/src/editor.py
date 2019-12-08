from src.ast_tokens import get_imports, count_imported_names, locate_import_ends


def transfer_mvdefs(src_path, dst_path, imports, mvdefs, src_agenda, dst_agenda):
    # ----------------------- First move the imports --------------------------
    # Do not need to handle "copy", "keep", or "stay" edit_agenda entries,
    # "copy" entries in src_agenda are mirrored by "echo" entries in dst_agenda
    for mv_i in dst_agenda.get("take"):
        # Transfer mv_i into the destination file: receive "move" as "take"
        pass
    for mv_i in src_agenda.get("move"):
        # Remove mv_i (imported name marked "move") from the source file
        pass
    for cp_i in dst_agenda.get("echo"):
        # Transfer cp_i into the destination file: receive "copy" as "echo"
        pass
    for rm_i in src_agenda.get("lose"):
        # Remove rm_i (imported name marked "lose") from the source file
        pass
    for rm_i in dst_agenda.get("lose"):
        # Remove rm_i (imported name marked "lose") from the source file
        pass
    # ------------------------ Next move the mvdefs ---------------------------
    # TODO: maybe make a def_edit_agenda for src and dst too ?
    return
