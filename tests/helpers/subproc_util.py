from subprocess import CompletedProcess, run

__all__ = ["pick_cmd", "subproc_cmd_from_argv"]


def pick_cmd(*, cp_: bool, ls_: bool) -> str:
    match [cp_, ls_]:
        case [(False | True), True]:
            cmd = "lsdef"
        case [True, False]:
            cmd = "cpdef"
        case [False, False]:
            cmd = "mvdef"
        case otherwise:
            raise ValueError(otherwise)
    return cmd


def subproc_cmd_from_argv(
    argv: list[str], *, cp_: bool = False, ls_: bool = False
) -> CompletedProcess:
    cmd_name = pick_cmd(cp_=cp_, ls_=ls_)
    proc = run([cmd_name, *argv], capture_output=True)
    return proc
