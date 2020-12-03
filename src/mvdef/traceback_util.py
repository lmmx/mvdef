from pathlib import Path


def pprint_stack_trace(stack):
    print(pformat_stack_trace(stack))


def pformat_stack_trace(stack):
    return "\n".join([pformat_frame_summary(fs) for fs in stack])


def pformat_frame_summary(frame_summary):
    filename = Path(frame_summary.filename).name
    name = frame_summary.name
    lineno = frame_summary.lineno
    line = frame_summary.line
    return f" ⇢ [{filename}] {name}@L{lineno} ⠶\n    `{line}`"
