from .editor_util import get_def_lines, get_defrange, excise_def_lines, overwrite_import
from .import_util import get_import_stmt_str

__all__ = [
    "nix_surplus_imports",
    "shorten_imports",
    "receive_imports",
    "copy_src_defs_to_dst",
    "remove_copied_defs",
    "transfer_mvdefs",
]


def nix_surplus_imports(self, record_removed_import_n=False):
    """
    Remove imports marked in the agenda as "lose" (src/dst) or "move" (src only).

    Bound as a method of `SrcFile`/`DstFile` classes, and used within `transfer_mvdefs`
    in step 1 part 1 (dst: removed_import_n) & step 5 part 1 (src: no removed_import_n).
    """
    # print("Step 1: Remove imports marked dst⠶lose")
    # print("Step 5: Remove imports marked src⠶{move,lose}")
    self.removed_import_n = []
    for rm_i in self.rm_agenda:  # sets .rm_agenda
        # Remove rm_i (imported name marked "lose" for dst, or marked "move"/"lose" for
        # dst) from the destination or source file using the line numbers of `self.trunk`,
        # computed as `dst.imports` by `get_imports`
        # (a destructive operation, so line numbers of `self.trunk` no longer valid),
        # if the removal of the imported name leaves no other imports on a line,
        # otherwise shorten that line by removing the import alias(es) marked "lose"
        info = self.rm_agenda.get(rm_i)
        imp_src_ending = info.get("import").split(".")[-1]
        # Retrieve the index of the line in import list
        rm_i_n = info.get("n")
        rm_i_linecount = self.import_counts[rm_i_n]
        if rm_i_linecount > 1:
            # This means there is ≥1 other import alias in the import statement
            # for this name, so remove it from it (i.e. "shorten" the statement.
            info["shorten"] = info.get("n_i")
        else:
            # This means there is nothing from this module being imported yet, so
            # must remove entire import statement (i.e. delete entire line range)
            if record_removed_import_n:
                # self is DstFile
                self.removed_import_n.append(rm_i_n)
            else:
                # self is SrcFile
                info["shorten"] = None
            imp_startline = self.imports[rm_i_n].first_token.start[0]
            imp_endline = self.imports[rm_i_n].last_token.end[0]
            imp_linerange = [imp_startline - 1, imp_endline]
            for i in range(*imp_linerange):
                self.lines[i] = None
            info["shorten"] = None


def shorten_imports(self, record_removed_import_n=False):
    """
    Shorten the imports based on the annotations set by `nix_surplus_imports`
    (potentially removing an import statement entirely if its list of imported
    names becomes shortened to 0).

    Bound as a method of `SrcFile`/`DstFile` classes, and used within `transfer_mvdefs`
    in step 1 part 2 (dst: removed_import_n) & step 5 part 2 (src: no removed_import_n).
    """
    self.to_shorten = {}
    for rm_i in self.rm_agenda:
        if self.rm_agenda.get(rm_i).get("shorten") is not None:
            self.to_shorten.update({rm_i: self.rm_agenda.get(rm_i)})
    self.n_to_short = set([self.to_shorten.get(x).get("n") for x in self.to_shorten])
    # Group all names being shortened that are of a common import statement
    for n in self.n_to_short:
        names_to_short = [
            x for x in self.to_shorten if self.to_shorten.get(x).get("n") == n
        ]
        n_i_to_short = [self.to_shorten.get(a).get("n_i") for a in names_to_short]
        # Rewrite `self.imports[n]` with all aliases except those in `names_to_short`
        imp_module = self.modules[n]
        pre_imp = self.imports[n]
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
            if record_removed_import_n:
                # All dst import aliases were removed, so remove entire import statement
                self.removed_import_n.append(n)
            imp_startline = pre_imp.first_token.start[0]
            imp_endline = pre_imp.last_token.end[0]
            imp_linerange = [imp_startline - 1, imp_endline]
            for i in range(*imp_linerange):
                self.lines[i] = None
        else:
            imp_stmt_str = get_import_stmt_str(shortened_alias_list, imp_module)
            overwrite_import(pre_imp, imp_stmt_str, self.lines)


def receive_imports(link):
    """
    Receive imports marked in the `link.dst.rcv_agenda`.

    Bound as a method of the `FileLink` class, and used in step 2 of `transfer_mvdefs`.
    """
    # print("Step 2: Add imports marked dst⠶{move,copy}")
    for rc_i in link.dst.rcv_agenda:  # sets rcv_agenda
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
    link.dst.to_extend = {}
    for rc_i in link.dst.rcv_agenda:
        if link.dst.rcv_agenda.get(rc_i).get("extend") is not None:
            link.dst.to_extend.update({rc_i: link.dst.rcv_agenda.get(rc_i)})
    link.dst.n_to_extend = set(
        [link.dst.to_extend.get(x).get("n") for x in link.dst.to_extend]
    )
    # Group all names being added as extensions that are of a common import statement
    for n in link.dst.n_to_extend:
        names_to_extend = [
            x for x in link.dst.to_extend if link.dst.to_extend.get(x).get("n") == n
        ]
        # Rewrite `link.dst.imports[n]` to include the aliases in `names_to_extend`
        imp_module = link.dst.modules[n]
        pre_imp = link.dst.imports[n]
        extended_alias_list = [(a.name, a.asname) for a in pre_imp.names]
        for rc_i in names_to_extend:
            dst_info = link.dst.to_extend.get(rc_i)
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
    link.dst.import_n = [
        n for n, _ in enumerate(link.dst.imports) if n not in link.dst.removed_import_n
    ]
    # sets .imports ⇢ sets .trunk
    if len(link.dst.import_n) == 0:
        # Place any new import statements at the start of the file, as none exist yet
        link.dst.last_imp_end = (
            0  # 1-based index logic: this means "before the first line"
        )
    else:
        last_import = link.dst.imports[link.dst.import_n[-1]]
        link.dst.last_imp_end = last_import.last_token.end[0]  # Leave in 1-based index
    # Collect import statements to insert after the last one
    link.dst._ins_imp_stmts = []
    link.dst._seen_multimodule_imports = set()
    for rc_i in link.dst.rcv_agenda:
        dst_info = link.dst.rcv_agenda.get(rc_i)
        if (
            rc_i in link.dst._seen_multimodule_imports
            or dst_info.get("extend") is not None
        ):
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
            if r == rc_i or None in [rc_i_module, r_src_module]:
                continue
            if r_src_module == rc_i_module:
                link.dst._seen_multimodule_imports.add(r)
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
        link.dst._ins_imp_stmts.append(imp_stmt_str)
    link.dst.lines = (
        link.dst.lines[: link.dst.last_imp_end]
        + link.dst._ins_imp_stmts
        + link.dst.lines[link.dst.last_imp_end :]
    )
    # sets dst.lines


def copy_src_defs_to_dst(link):
    """
    Transfer mvdef into the destination file i.e. 'receive mvdef', where mvdef is an
    `ast.FunctionDefinition` node with start/end position annotations using the line
    numbers of `link.src.trunk`, computed as `link.src.defs_to_move` by
    `.ast_tokens.get_defs` (in the `hasattr` check block of the
    `.transfer.SrcFile.defs_to_move` property itself). This is an append operation, so
    line numbers from `link.src.trunk` remain valid.

    Bound as a method of the `FileLink` class, and used in step 3 of `transfer_mvdefs`.
    """
    #print("Step 3: copy function definitions {mvdefs} from src to dst")
    # The following line sets .defs_to_move ⇢ sets .trunk ⇢ sets .lines
    link.set_src_defs_to_move()
    for mvdef in link.src.defs_to_move:
        indent = 4
        # Simply add an indent for each AST path part (i.e. per classdef/funcdef)
        dst_col_offset = indent * len(mvdef.into_path.parts) if mvdef.into_path else 0
        # Transfer mvdef into the destination file: receive mvdef
        #print(f"{mvdef=}")
        def_startline, def_endline = get_defrange(mvdef)
        deflines = link.src.lines[def_startline:def_endline]
        # get_def_lines prepares the lines (whitespace and indentation)
        indent_delta = dst_col_offset - mvdef.col_offset
        if mvdef.into_path:
            if not hasattr(mvdef.into_path, "node"):
                raise NotImplementedError(f"{mvdef.into_path.string} has no node")
            into_end = mvdef.into_path.node.end_lineno
            pre_lines = link.dst.lines[:into_end]
            post_lines = link.dst.lines[into_end:]
            new_lines = get_def_lines(deflines, link.dst.lines, True, indent_delta)
            if [l for l in post_lines if l]: # check non-empty, ignoring `None` values
                if len(post_lines) > 1:
                    it = iter(map(str.rstrip, post_lines))
                    if any(it): # consume generator up to the first nonblank line
                        first_nonblank_i = len(post_lines) - len([*it]) - 1
                        window_size = 1 if post_lines[first_nonblank_i][0] == " " else 2
                        if first_nonblank_i < window_size:
                            # if first following nonblank line is indented, 1 else 2
                            window_filler = window_size - first_nonblank_i
                            for _ in range(window_filler):
                                post_lines.insert(0, "\n")
                    else:
                        pass # all remaining lines are blank!
            link.dst.lines = pre_lines + new_lines + post_lines
        else:
            append_lines = get_def_lines(deflines, link.dst.lines, False, indent_delta)
            #breakpoint()
            link.dst.lines += append_lines
        if not link.dst.is_edited:
            link.dst.is_edited = True


def remove_copied_defs(src):
    """
    Remove function definitions marked as to move from the source file, i.e.
    after copying them in step 3.

    Bound as a method of the `SrcFile` class, and used within `transfer_mvdefs`.
    """
    # print("Step 4: Remove function definitions {mvdefs} from src")
    for mvdef in sorted(
        src.defs_to_move, key=lambda d: d.last_token.end[0], reverse=True
    ):
        # Remove mvdef (function def. marked "mvdef") from the source file
        excise_def_lines(mvdef, src.lines)
        if not src.is_edited:
            src.is_edited = True


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
    link.dst.nix_surplus_imports(record_removed_import_n=True)
    link.dst.shorten_imports(record_removed_import_n=True)
    #
    # --------------- STEP 2: ADD IMPORTS MARKED DST⠶{MOVE,COPY} --------------------
    #
    link.receive_imports()
    # ------------------------------------------------------------------------------
    # Postpone the extension/addition of import statements (do all at once so as to
    # retain meaningful line numbers, as changing one at a time would ruin index)
    # as well as to minimise file handle opening/reopening since that IO takes time
    # Also: sort the import statements by n in `link.src.imports` index to retain order
    # ------------------------------------------------------------------------------
    #
    # --------- STEP 3: COPY FUNCTION DEFINITIONS {MVDEFS} FROM SRC TO DST ---------
    #
    link.copy_src_defs_to_dst()
    # -------- Line number preservation no longer needed, only now modify src -------
    # Iterate through funcdefs in reverse line number order (i.e. upward from bottom)
    # using the line numbers of `link.src.trunk`, computed as `link.src.defs_to_move` by
    # `.ast_tokens.get_defs`
    #
    # --------- STEP 4: REMOVE FUNCTION DEFINITIONS {MVDEFS} FROM SRC ---------
    #
    link.src.remove_copied_defs()
    #
    # --------------- STEP 5: REMOVE IMPORTS MARKED SRC⠶{MOVE,LOSE} ----------------
    #
    link.src.nix_surplus_imports()
    link.src.shorten_imports()
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
