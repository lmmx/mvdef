from src.ast_tokens import get_imports, count_imported_names, locate_import_ends

def edit_defs(src_path, dst_path, imports, defs, edit_agenda):
    for mvdef in edit_agenda.get("move"):
        # Move the mvdefs out of the source file
        pass
    for cpdef in edit_agenda.get("copy"):
        # Copy the cpdefs over
        pass
    for rmdef in edit_agenda.get("lose"):
        # Just comment out the rmdefs for now
        pass
    return
