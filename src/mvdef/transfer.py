from .ast_tokens import set_defs_to_move, get_imports, get_tree
from .ast_util import (
    retrieve_ast_agenda,
    process_ast,
    parse_mv_funcs,
    get_def_names,
    set_nondef_names,
    set_intradef_names,
    set_methdef_names,
    set_extradef_names,
)
from .backup import backup
from .colours import colour_str as colour
from .editor import (
    nix_surplus_imports,
    shorten_imports,
    receive_imports,
    copy_src_defs_to_dst,
    remove_copied_defs,
    transfer_mvdefs,
)
from .import_util import count_imported_names, get_module_srcs, imp_def_subsets
from itertools import chain

# from .traceback_util import pprint_stack_trace
from sys import stderr
from traceback import print_stack, extract_stack, format_list

__all__ = ["LinkedFile", "SrcFile", "DstFile", "FileLink", "parse_transfer"]


class LinkedFile:
    def __init__(self, path, report, nochange, use_backup, mvdefs, into_paths):
        self.path = path
        self.report = report
        self.nochange = nochange
        self.use_backup = use_backup
        self.mvdefs = mvdefs
        self.into_paths = into_paths

    is_edited = False

    def backup(self, dry_run):
        assert backup(self.path, dry_run=dry_run)

    @property
    def edits(self):
        return self._edits

    @edits.setter
    def edits(self, e):
        self._edits = e

    @property
    def path(self):
        return self._p if hasattr(self, "_p") else None

    @path.setter
    def path(self, p):
        self._p = p

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, report):
        self._report = report

    @property
    def nochange(self):
        return self._nochange

    @nochange.setter
    def nochange(self, nochange):
        self._nochange = nochange

    @property
    def use_backup(self):
        return self._use_backup

    @use_backup.setter
    def use_backup(self, use_backup):
        self._use_backup = use_backup

    @property
    def mvdefs(self):
        return self._mvdefs

    @mvdefs.setter
    def mvdefs(self, mvdefs):
        self._mvdefs = mvdefs

    @property
    def into_paths(self):
        return self._into_paths

    @into_paths.setter
    def into_paths(self, into_paths):
        self._into_paths = into_paths

    @property
    def is_extant(self):
        return self.path.exists() and self.path.is_file()

    retrieve_ast_agenda = retrieve_ast_agenda
    process_ast = process_ast  # called by `retrieve_ast_agenda`
    parse_mv_funcs = parse_mv_funcs  # called by `process_ast`
    imp_def_subsets = imp_def_subsets  # called by `process_ast`
    get_def_names = get_def_names
    set_nondef_names = set_nondef_names
    set_intradef_names = set_intradef_names
    set_methdef_names = set_methdef_names
    set_extradef_names = set_extradef_names

    @property
    def undef_names(self):
        "undef_names contains only those names that are imported but never used"
        if not hasattr(self, "nondef_names"):
            raise ValueError("Cannot use undef_names before setting nondef_names")
        elif not hasattr(self, "_undef_names"):
            self.set_undef_names()
        else:
            return self._undef_names

    @undef_names.setter
    def undef_names(self, undef_names):
        self._undef_names = undef_names

    def set_undef_names(self):
        self.undef_names = {
            x: self.nondef_names.get(x)
            for x in self.nondef_names
            if x not in self.extradef_names
        }

    def ast_parse(self, transfers=None):
        "Create edit agendas from the parsed AST of source and destination files"
        assert self.path, f"'{type(self).__name__}.path' not set"
        self.retrieve_ast_agenda(transfers)  # parse AST, populate the edits property
        self.validate_edits()
        if self.report:
            self.report_edits()
        return

    @property
    def trunk(self):
        if not hasattr(self, "_trunk"):
            # print(f"SETTING TRUNK ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.set_trunk()
        return self._trunk

    @trunk.setter
    def trunk(self, trunk):
        self._trunk = trunk

    def set_trunk(self):
        self.trunk = get_tree(self.path).body

    @property
    def lines(self):
        if not hasattr(self, "_lines"):
            # print(f"SETTING LINES ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.readlines()
        return self._lines

    @lines.setter
    def lines(self, lines):
        self._lines = lines

    def readlines(self):
        with open(self.path, "r") as f:
            self.lines = f.readlines()

    @property
    def imports(self):
        if not hasattr(self, "_imports"):
            # print(f"SETTING IMPORTS ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.imports = get_imports(self.trunk, trunk_only=True)
        return self._imports

    @imports.setter
    def imports(self, imports):
        self._imports = imports

    @property
    def import_counts(self):
        if not hasattr(self, "_import_counts"):
            # print(f"SETTING IMPORT_COUNTS ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.import_counts = count_imported_names(self.imports)
        return self._import_counts

    @import_counts.setter
    def import_counts(self, counts):
        self._import_counts = counts

    @property
    def modules(self):
        if not hasattr(self, "_modules"):
            # print(f"SETTING MODULES ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.modules = get_module_srcs(self.imports)
        return self._modules

    @modules.setter
    def modules(self, modules):
        self._modules = modules

    def get_merged_dicts(self, categories):
        """
        Return the first item in each agenda category (without list expanding).
        Used when we no longer need to keep a record of a name's annotation.
        """
        return dict(
            [
                next(iter(a.items()))
                for a in [*chain.from_iterable(map(self.edits.get, categories))]
            ]
        )


class SrcFile(LinkedFile):
    def validate_edits(self):
        e_msg = f"The {self.__class__.__name__} did not return a processed AST"
        assert self.edits, e_msg

    set_defs_to_move = set_defs_to_move

    @property
    def defs_to_move(self):
        if not hasattr(self, "_defs_to_move"):
            self.set_defs_to_move() # sets defs_to_move
        return self._defs_to_move

    @defs_to_move.setter
    def defs_to_move(self, defs):
        self._defs_to_move = defs

    def set_rm_agenda(self):
        "Merge lose/move lists of info dicts into dict of to-be-removed names/info"
        self.rm_agenda = self.get_merged_dicts(["move", "lose"])

    @property
    def rm_agenda(self):
        if not hasattr(self, "_rm_agenda"):
            # print(f"SETTING RM_AGENDA ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.set_rm_agenda()
        return self._rm_agenda

    @rm_agenda.setter
    def rm_agenda(self, agenda):
        self._rm_agenda = agenda

    def report_edits(self):
        c_str = colour("light_gray", self.path)
        if self.into_paths:
            _as = f" ({[f'as {x}' if x else '—' for x in self.into_paths]})"
        else:
            _as = ""
        print(f"⇒ Functions moving from {c_str}: {self.mvdefs}{_as}", file=stderr)

    nix_surplus_imports = nix_surplus_imports
    shorten_imports = shorten_imports
    remove_copied_defs = remove_copied_defs


class DstFile(LinkedFile):
    def validate_edits(self):
        pass  # it's valid for there not to be a destination file and hence no processed AST

    def ensure_exists(self):
        "Create the destination file if it doesn't exist, and if this isn't a dry run"
        if not self.is_extant and not self.nochange:
            open(self.path, "w").close()

    def set_rcv_agenda(self):
        "Merge take/echo lists of info dicts into dict of received names/info"
        self.rcv_agenda = self.get_merged_dicts(["take", "echo"])

    @property
    def rcv_agenda(self):
        if not hasattr(self, "_rcv_agenda"):
            # print(f"SETTING RCV_AGENDA ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.set_rcv_agenda()
        return self._rcv_agenda

    @rcv_agenda.setter
    def rcv_agenda(self, agenda):
        self._rcv_agenda = agenda

    def set_rm_agenda(self):
        "Convert lose list of info dicts into dict of to-be-removed names/info"
        self.rm_agenda = self.get_merged_dicts(["lose"])

    @property
    def rm_agenda(self):
        if not hasattr(self, "_rm_agenda"):
            # print(f"SETTING RM_AGENDA ON {self}")
            # stack = extract_stack()
            # pprint_stack_trace(stack)
            self.set_rm_agenda()
        return self._rm_agenda

    @rm_agenda.setter
    def rm_agenda(self, agenda):
        self._rm_agenda = agenda

    def report_edits(self):
        c_str = colour("light_gray", self.path)
        if self.edits:
            print(f"⇒ Functions will move to {c_str}")
        else:
            # There is no destination file (it will be created)
            print(
                (f"⇒ Functions will move to {c_str} (it's being created from them)"),
                file=stderr,
            )

    nix_surplus_imports = nix_surplus_imports
    shorten_imports = shorten_imports


class FileLink:
    def __init__(self, mvdefs, into_paths, src_p, dst_p, report, nochange, test_func, use_backup):
        self.mvdefs = mvdefs
        self.into_paths = into_paths
        self.report = report
        self.nochange = nochange
        # print("Setting link")
        self.set_link(src_p, dst_p, use_backup=use_backup)
        self.use_backup = use_backup  # will create backups (now!) if True
        self.test_func = test_func  # will run the test_func to check it works
        try:
            # print("Running link.src.ast_parse()")
            self.src.ast_parse()  # populate self.src.edits
        except Exception as e:
            self.src.edits = e
            return
        # print("Running link.dst.ensure_exists")
        self.dst.ensure_exists()
        self.set_src_defs_to_move()
        transfers = {
            "take": self.src.edits.get("move"),
            "echo": self.src.edits.get("copy"),
        }
        try:
            # print("Running link.dst.ast_parse(transfers)")
            self.dst.ast_parse(transfers=transfers)  # populate self.dst.edits
            #breakpoint()
        except Exception as e:
            self.dst.edits = e
            return

    def set_link(self, src_p, dst_p, use_backup, report=None, nochange=None):
        nochange = self.nochange if nochange is None else nochange
        report = self.report if report is None else report
        self.src = SrcFile(src_p, report=report, nochange=nochange, use_backup=use_backup, mvdefs=self.mvdefs, into_paths=self.into_paths)
        self.dst = DstFile(dst_p, report=report, nochange=nochange, use_backup=use_backup, mvdefs=None, into_paths=None)

    def set_src_defs_to_move(self):
        self.src.set_defs_to_move(self.dst)

    @property
    def mvdefs(self):
        return self._mvdefs

    @mvdefs.setter
    def mvdefs(self, mvdefs):
        self._mvdefs = mvdefs

    @property
    def report(self):
        return self._report

    @report.setter
    def report(self, report):
        self._report = report

    @property
    def nochange(self):
        return self._nochange

    @nochange.setter
    def nochange(self, nochange):
        self._nochange = nochange

    @property
    def use_backup(self):
        return self._use_backup

    @use_backup.setter
    def use_backup(self, use_backup):
        self._use_backup = use_backup
        if use_backup:
            self.backup(dry_run=self.nochange)

    @property
    def test_func(self):
        return self._test_func

    @test_func.setter
    def test_func(self, test_func):
        if test_func is not None:
            try:
                test_func.__call__()
            except AssertionError as e:
                raise RuntimeError(
                    f"! '{test_func.__name__}' failed, aborting mvdef execution."
                )
        self._test_func = test_func

    def backup(self, dry_run):
        "Run individual backup checks for src and dst"
        self.src.backup(dry_run=dry_run)
        self.dst.backup(dry_run=dry_run)

    receive_imports = receive_imports
    copy_src_defs_to_dst = copy_src_defs_to_dst
    transfer_mvdefs = transfer_mvdefs


# TODO: Move parse_example to AST once logic is figured out for the demo
def parse_transfer(
    src_p, dst_p, mvdefs, into_paths, test_func=None, report=True, nochange=True, use_backup=True
):
    """
    Execute the transfer of function definitions and import statements, optionally
    (if test_func is specified) also calls that afterwards to confirm functionality
    remains intact.

    If test_func is specified, it must only use AssertionError (i.e. you are free
    to have the test_func call other functions, but it must catch any errors therein
    and only raise errors from assert statements). This is to simplify this step.
    My example would be to list one or more failing tests, then assert that this
    list is None, else raise an AssertionError of these tests' definition names
    (see example.test.test_demo⠶test_report for an example of such a function).

    If nochange is False, files will be changed in place (i.e. setting it
    to False is equivalent to setting the edit parameter to True).
      - Note: this was unimplemented...

    This parameter is used as a sanity check to prevent wasted computation,
    as if neither report is True nor nochange is False, there is nothing to do.
    """
    # Backs up source and target to a hidden file, restorable in case of error,
    # and creating a hidden placeholder if the target doesn't exist yet
    assert True in [report, not nochange], "Nothing to do"
    link = FileLink(mvdefs, into_paths, src_p, dst_p, report, nochange, test_func, use_backup)
    # Raise any error encountered when building the AST
    if isinstance(link.src.edits, Exception):
        global src_err_link
        src_err_link = link
        raise link.src.edits
    elif isinstance(link.dst.edits, Exception):
        global dst_err_link
        dst_err_link = link
        raise link.dst.edits
    # print("Finished checking agenda: no exceptions found")
    if nochange:
        print("DRY RUN: No files have been modified, skipping tests.", file=stderr)
        return link.src.edits, link.dst.edits
    else:
        # Edit the files (no longer pass imports or defs, will recompute AST)
        # print("Transferring mvdefs over the link")
        link.transfer_mvdefs()
    if test_func is None:
        return link.src.edits, link.dst.edits
    else:
        try:
            test_func.__call__()
        except AssertionError as e:
            # TODO: implement backup restore
            print(
                (
                    f"! '{test_func.__name__}' failed, indicating changes made by mvdef broke the"
                    "program (if backups used, mvdefs will now attempt to restore)"
                ),
                file=stderr,
            )
            raise RuntimeError(e)
    return link.src.edits, link.dst.edits
