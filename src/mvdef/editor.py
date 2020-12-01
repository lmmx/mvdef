from .editor_util import get_def_lines, get_defrange, excise_def_lines, overwrite_import
from .import_util import get_import_stmt_str
from .debugging import debug_here

__all__ = ["transfer_mvdefs"]

def transfer_mvdefs(link):
    ## Firstly annotate ASTs with the asttokens library
    # ------------------------- First move the imports ------------------------------
    # Do not need to handle "copy", "keep", or "stay" edit_agenda entries,
    # "copy" entries in link.src.edits are mirrored by "echo" entries in link.dst.edits,
    # while all "move" entries in link.src.edits are mirrored as "take" in link.dst.edits
    # -------------------------------------------------------------------------------
    # The code that was here is now in the property methods of `SrcFile` and `DstFile`.
    #
    # The `edits` attribute of `link.src` and `link.dst` are now used to create the
    # `src.rm_agenda`, `dst.rcv_agenda`, and `dst.rm_agenda` upon first access of the
    # property (implicitly), and this access takes place in the following function:
    # ----------------- STEP 1: REMOVE IMPORTS MARKED DST⠶LOSE ----------------------
    #
    removed_import_n = []
    for rm_i in link.dst.rm_agenda:
        # Remove rm_i (imported name marked "lose") from the destination file using
        # the line numbers of `link.dst.trunk`, computed as `link.dst.imports` by `get_imports`
        # (a destructive operation, so line numbers of `link.dst.trunk` no longer valid),
        # if the removal of the imported name leaves no other imports on a line,
        # otherwise shorten that line by removing the import alias(es) marked "lose"
        dst_info = link.dst.rm_agenda.get(rm_i)
        imp_src_ending = dst_info.get("import").split(".")[-1]
        # Retrieve the index of the line in import list
        rm_i_n = dst_info.get("n")
        rm_i_linecount = link.dst.import_counts[rm_i_n]
        if rm_i_linecount > 1:
            # This means there is ≥1 other import alias in the import statement
            # for this name, so remove it from it (i.e. "shorten" the statement.
            dst_info["shorten"] = dst_info.get("n_i")
        else:
            # This means there is nothing from this module being imported yet, so
            # must remove entire import statement (i.e. delete entire line range)
            removed_import_n.append(rm_i_n)
            imp_startline = link.dst.imports[rm_i_n].first_token.start[0]
            imp_endline = link.dst.imports[rm_i_n].last_token.end[0]
            imp_linerange = [imp_startline - 1, imp_endline]
            for i in range(*imp_linerange):
                link.dst.lines[i] = None
            dst_info["shorten"] = None
    to_shorten = {}
    for rm_i in link.dst.rm_agenda:
        if link.dst.rm_agenda.get(rm_i).get("shorten") is not None:
            to_shorten.update({rm_i: link.dst.rm_agenda.get(rm_i)})
    n_to_short = set([to_shorten.get(x).get("n") for x in to_shorten])
    # Group all names being shortened that are of a common import statement
    for n in n_to_short:
        names_to_short = [x for x in to_shorten if to_shorten.get(x).get("n") == n]
        n_i_to_short = [to_shorten.get(a).get("n_i") for a in names_to_short]
        # Rewrite `link.dst.imports[n]` with all aliases except those in `names_to_short`
        imp_module = link.dst.modules[n]
        pre_imp = link.dst.imports[n]
        shortened_alias_list = [(a.name, a.asname) for a in pre_imp.names]
        # Proceed backwards from the end to the start, permitting deletions by index
        for (name, asname) in shortened_alias_list[::-1]:
            if asname is None and name not in names_to_short:
                continue
            elif asname not in names_to_short:
                continue
            del_i = shortened_alias_list.index((name, asname))
            del shortened_alias_list[del_i]
        if len(shortened_alias_list) == 0:
            # All import aliases were removed, so remove the entire import statement
            removed_import_n.append(n)
            imp_startline = pre_imp.first_token.start[0]
            imp_endline = pre_imp.last_token.end[0]
            imp_linerange = [imp_startline - 1, imp_endline]
            for i in range(*imp_linerange):
                link.dst.lines[i] = None
        else:
            imp_stmt_str = get_import_stmt_str(shortened_alias_list, imp_module)
            overwrite_import(pre_imp, imp_stmt_str, link.dst.lines)
    #
    # --------------- STEP 2: ADD IMPORTS MARKED DST⠶{MOVE,COPY} --------------------
    #
    for rc_i in link.dst.rcv_agenda:
        # Transfer mv_i into the destination file: receive "move" as "take"
        # Transfer cp_i into the destination file: receive "copy" as "echo"
        dst_info = link.dst.rcv_agenda.get(rc_i)
        imp_src_ending = dst_info.get("import").split(".")[-1]
        # Use name/asname to retrieve the index of the line in import list to get
        # the module which is at the same index in the list of src modules:
        rc_i_n = dst_info.get("n")
        rc_i_module = link.src.modules[rc_i_n]
        # Compare the imported name to the module if one exists
        if rc_i_module is not None:
            dst_module_set = set(link.dst.modules).difference({None})
            if rc_i_module in dst_module_set:
                # This means there is already ≥1 ast.ImportFrom statement (i.e. a
                # line) which imports from the same module as the to-be-added import
                # name does, so combine it with this existing line. Assume the 1st
                # such ImportFrom is to be extended (ignoring other possible ones).
                dst_info["extend"] = link.dst.modules.index(rc_i_module)
            else:
                # This means there is nothing from this module being imported yet,
                # so must create a new ImportFrom statement (i.e. a new line)
                dst_info["extend"] = None
        else:
            # This means `rc_i` is an ast.Import statement, not ImportFrom
            # (PEP8 recommends separate imports, so do not extend another)
            dst_info["extend"] = None
    to_extend = {}
    for rc_i in link.dst.rcv_agenda:
        if link.dst.rcv_agenda.get(rc_i).get("extend") is not None:
            to_extend.update({rc_i: link.dst.rcv_agenda.get(rc_i)})
    n_to_extend = set([to_extend.get(x).get("n") for x in to_extend])
    # Group all names being added as extensions that are of a common import statement
    for n in n_to_extend:
        names_to_extend = [x for x in to_extend if to_extend.get(x).get("n") == n]
        # Rewrite `link.dst.imports[n]` to include the aliases in `names_to_extend`
        imp_module = link.dst.modules[n]
        pre_imp = link.dst.imports[n]
        extended_alias_list = [(a.name, a.asname) for a in pre_imp.names]
        for rc_i in names_to_extend:
            dst_info = to_extend.get(rc_i)
            imp_src = dst_info.get("import")
            imp_src_ending = imp_src.split(".")[-1]
            if rc_i == imp_src_ending:
                rc_i_name, rc_i_as = rc_i, None
            elif imp_module is not None:
                rc_i_name, rc_i_as = imp_src_ending, rc_i
            else:
                rc_i_name, rc_i_as = imp_src, rc_i
            extended_alias_list.append((rc_i_name, rc_i_as))
        imp_stmt_str = get_import_stmt_str(extended_alias_list, imp_module)
        overwrite_import(pre_imp, imp_stmt_str, link.dst.lines)
    # Next, put any import names marked "take" or "echo" that are not extensions
    # of existing import statements into new lines (this breaks the line index).
    #
    # Firstly, find the insertion point for new import statements by re-processing
    # the list of lines (default to start of file if it has no import statements)
    import_n = [n for n, _ in enumerate(link.dst.imports) if n not in removed_import_n]
    if len(import_n) == 0:
        # Place any new import statements at the start of the file, as none exist yet
        last_imp_end = 0  # 1-based index logic: this means "before the first line"
    else:
        last_import = link.dst.imports[import_n[-1]]
        last_imp_end = last_import.last_token.end[0]  # Leave in 1-based index
    ins_imp_stmts = []  # Collect import statements to insert after the last one
    seen_multimodule_imports = set()
    for rc_i in link.dst.rcv_agenda:
        dst_info = link.dst.rcv_agenda.get(rc_i)
        if rc_i in seen_multimodule_imports or dst_info.get("extend") is not None:
            continue
        imp_src = dst_info.get("import")
        imp_src_ending = imp_src.split(".")[-1]
        rc_i_n = dst_info.get("n")
        rc_i_module = link.src.modules[rc_i_n]
        if rc_i == imp_src_ending:
            rc_i_name, rc_i_as = rc_i, None
        elif rc_i_module is not None:
            rc_i_name, rc_i_as = imp_src_ending, rc_i
        else:
            rc_i_name, rc_i_as = imp_src, rc_i
        alias_list = [(rc_i_name, rc_i_as)]
        for r in link.dst.rcv_agenda:
            r_src_module = link.src.modules[link.dst.rcv_agenda.get(r).get("n")]
            if r == rc_i or None in [rc_i_module, r_src_module]: continue
            if r_src_module == rc_i_module:
                seen_multimodule_imports.add(r)
                r_dst_info = link.dst.rcv_agenda.get(r)
                r_imp_src = r_dst_info.get("import")
                r_imp_src_ending = r_imp_src.split(".")[-1]
                r_n = r_dst_info.get("n")
                r_module = link.src.modules[r_n]
                if r == r_imp_src_ending:
                    r_name, r_as = r, None
                elif r_module is not None:
                    r_name, r_as = r_imp_src_ending, r
                else:
                    r_name, r_as = r_dst_info.get("import"), r
                alias_list.append((rc_i_name, rc_i_as))
        # Create the Import or ImportFrom statement
        imp_stmt_str = get_import_stmt_str(alias_list, rc_i_module)
        ins_imp_stmts.append(imp_stmt_str)
    link.dst.lines = link.dst.lines[:last_imp_end] + ins_imp_stmts + link.dst.lines[last_imp_end:]
    # ------------------------------------------------------------------------------
    # Postpone the extension/addition of import statements (do all at once so as to
    # retain meaningful line numbers, as changing one at a time would ruin index)
    # as well as to minimise file handle opening/reopening since that IO takes time
    # Also: sort the import statements by n in `link.src.imports` index to retain order
    # ------------------------------------------------------------------------------
    #
    # --------- STEP 3: COPY FUNCTION DEFINITIONS {MVDEFS} FROM SRC TO DST ---------
    #
    for mvdef in link.src.defs_to_move:
        # Transfer mvdef into the destination file: receive mvdef
        # mvdef is an ast.FunctionDefinition node with start/end position annotations
        # using the line numbers of `link.src.trunk`, computed as
        # `link.src.defs_to_move` by `.ast_tokens.get_defs` (in the `hasattr` check
        # block of `.transfer.SrcFile.defs_to_move` itself)
        # (this is an append operation, so line numbers from `link.src.trunk` remain valid)
        def_startline, def_endline = get_defrange(mvdef)
        deflines = link.src.lines[def_startline:def_endline]
        link.dst.lines += get_def_lines(deflines, link.dst.lines)
        if not link.dst.is_edited:
            link.dst.is_edited = True
    # -------- Line number preservation no longer needed, only now modify src -------
    # Iterate through funcdefs in reverse line number order (i.e. upward from bottom)
    # using the line numbers of `link.src.trunk`, computed as `link.src.defs_to_move` by
    # `.ast_tokens.get_defs`
    #
    # --------- STEP 4: REMOVE FUNCTION DEFINITIONS {MVDEFS} FROM SRC ---------
    #
    for mvdef in sorted(link.src.defs_to_move, key=lambda d: d.last_token.end[0], reverse=True):
        # Remove mvdef (function def. marked "mvdef") from the source file
        excise_def_lines(mvdef, link.src.lines)
        if not link.src.is_edited:
            link.src.is_edited = True
    #
    # --------------- STEP 5: REMOVE IMPORTS MARKED SRC⠶{MOVE,LOSE} ----------------
    #
    for rm_i in link.src.rm_agenda:
        # Remove rm_i (imported name marked "move"/"lose") from the source file using
        # the line numbers of `link.src.trunk`, computed as `link.src.imports` by `get_imports`
        # (a destructive operation, so line numbers of `link.src.trunk` no longer valid),
        # if the removal of the imported name leaves no other imports on a line,
        # otherwise shorten that line by removing the import alias(es) marked "lose"
        src_info = link.src.rm_agenda.get(rm_i)
        imp_src_ending = src_info.get("import").split(".")[-1]
        # Retrieve the index of the line in import list
        rm_i_n = src_info.get("n")
        rm_i_linecount = link.src.import_counts[rm_i_n]
        if rm_i_linecount > 1:
            # This means there is ≥1 other import alias in the import statement
            # for this name, so remove it from it (i.e. "shorten" the statement.
            src_info["shorten"] = src_info.get("n_i")
        else:
            # This means there is nothing from this module being imported yet, so
            # must remove entire import statement (i.e. delete entire line range)
            src_info["shorten"] = None
            imp_startline = link.src.imports[rm_i_n].first_token.start[0]
            imp_endline = link.src.imports[rm_i_n].last_token.end[0]
            imp_linerange = [imp_startline - 1, imp_endline]
            for i in range(*imp_linerange):
                link.src.lines[i] = None
            src_info["shorten"] = None
    to_shorten = {}
    for rm_i in link.src.rm_agenda:
        if link.src.rm_agenda.get(rm_i).get("shorten") is not None:
            to_shorten.update({rm_i: link.src.rm_agenda.get(rm_i)})
    n_to_short = set([to_shorten.get(x).get("n") for x in to_shorten])
    # Group all names being shortened that are of a common import statement
    for n in n_to_short:
        names_to_short = [x for x in to_shorten if to_shorten.get(x).get("n") == n]
        n_i_to_short = [to_shorten.get(a).get("n_i") for a in names_to_short]
        # Rewrite `link.src.imports[n]` with all aliases except those in `names_to_short`
        imp_module = link.src.modules[n]
        pre_imp = link.src.imports[n]
        shortened_alias_list = [(a.name, a.asname) for a in pre_imp.names]
        # Proceed backwards from the end to the start, permitting deletions by index
        for (name, asname) in shortened_alias_list[::-1]:
            if asname is None and name not in names_to_short:
                continue
            elif asname is not None and asname not in names_to_short:
                continue
            del_i = shortened_alias_list.index((name, asname))
            del shortened_alias_list[del_i]
        if len(shortened_alias_list) == 0:
            # All import aliases were removed, so remove the entire import statement
            imp_startline = pre_imp.first_token.start[0]
            imp_endline = pre_imp.last_token.end[0]
            imp_linerange = [imp_startline - 1, imp_endline]
            for i in range(*imp_linerange):
                link.src.lines[i] = None
        else:
            imp_stmt_str = get_import_stmt_str(shortened_alias_list, imp_module)
            overwrite_import(pre_imp, imp_stmt_str, link.src.lines)
    # Finish by writing line changes back to file (only if agenda shows edits made
    # or the `is_edited` flag was set in steps 3 or 4)
    if not link.src.is_edited and link.src.rm_agenda:
        link.src.is_edited = True
    if not link.dst.is_edited and (link.dst.rcv_agenda or link.dst.rm_agenda):
        link.dst.is_edited = True

    if link.src.is_edited:
        link.src.lines = "".join([line for line in link.src.lines if line is not None])
        with open(link.src.path, "w") as f:
            f.write(link.src.lines)
    if link.dst.is_edited:
        link.dst.lines = "".join([line for line in link.dst.lines if line is not None])
        with open(link.dst.path, "w") as f:
            f.write(link.dst.lines)
    return
