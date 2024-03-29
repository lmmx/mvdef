# mvdef

[![Documentation](https://readthedocs.org/projects/mvdef/badge/?version=latest)](https://mvdef.readthedocs.io/en/latest/)
[![CI Status](https://github.com/lmmx/mvdef/actions/workflows/master.yml/badge.svg)](https://github.com/lmmx/mvdef/actions/workflows/master.yml)
[![Coverage](https://codecov.io/gh/lmmx/mvdef/branch/master/graph/badge.svg)](https://codecov.io/github/lmmx/mvdef)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Package providing command line tools to move/copy function/classes and their associated import statements between files

[Read The Docs](https://mvdef.readthedocs.io/en/latest/)

## Requires

- Python 3.10+

## Installation

```sh
pip install mvdef
```

## Usage

### `mvdef`

Moves functions named by `-m`/`--mv` and their associated imports from `src` to `dst`,
or just previews the changes as a diff if passed `-d`/`--dry-run`.

```
usage: mvdef [-h] -m [MV ...] [-d] [-e] [-c] [-f] [-v] src dst

  Move function definitions from one file to another, moving/copying
  any necessary associated import statements along with them.

  Option     Description                                Type        Default
  —————————— —————————————————————————————————————————— ——————————— ———————
• src        source file to take definitions from       Path        -
• dst        destination file (may not exist)           Path        -
• mv         names to move from the source file         list[str]   -
• dry_run    whether to only preview the change diffs   bool        False
• escalate   whether to raise an error upon failure     bool        False
• cls_defs   whether to use only class definitions      bool        False
• func_defs  whether to use only function definitions   bool        False
• verbose    whether to log anything                    bool        False

positional arguments:
  src
  dst

options:
  -h, --help            show this help message and exit
  -m [MV ...], --mv [MV ...]
  -d, --dry-run
  -e, --escalate
  -c, --cls-defs
  -f, --func-defs
  -v, --verbose
```

### `cpdef`

Copies functions named by `-m`/`--mv` and their associated imports from `src` to `dst`,
or just previews the changes as a diff if passed `-d`/`--dry-run`.

Has the same flags and signature as `mvdef`, but never changes `src`.

```
usage: cpdef [-h] -m [MV ...] [-d] [-e] [-c] [-f] [-v] src dst

  Copy function definitions from one file to another, and any necessary
  associated import statements along with them.

  Option     Description                                Type        Default
  —————————— —————————————————————————————————————————— ——————————— ———————
• src        source file to copy definitions from       Path        -
• dst        destination file (may not exist)           Path        -
• mv         names to copy from the source file         list[str]   -
• dry_run    whether to only preview the change diffs   bool        False
• escalate   whether to raise an error upon failure     bool        False
• cls_defs   whether to use only class definitions      bool        False
• func_defs  whether to use only function definitions   bool        False
• verbose    whether to log anything                    bool        False

positional arguments:
  src
  dst

options:
  -h, --help            show this help message and exit
  -m [MV ...], --mv [MV ...]
  -d, --dry-run
  -e, --escalate
  -c, --cls-defs
  -f, --func-defs
  -v, --verbose
```

### `lsdef`

Has a similar signature, but no `dst` (it operates on just one file) and the `mv` argument
is replaced by `match`, which can specify regular expressions (default `*` matches any name).

```
usage: lsdef [-h] [-m [MATCH ...]] [-d] [-l] [-e] [-c] [-f] [-v] src

  List function definitions in a given file.

  Option     Description                                Type        Default
  —————————— —————————————————————————————————————————— ——————————— ———————
• src        source file to list definitions from       Path        -
• match      name regex to list from the source file    list[str]   ['*']
• dry_run    whether to print the __all__ diff          bool        False
• list       whether to print the list of names         bool        False
• escalate   whether to raise an error upon failure     bool        False
• cls_defs   whether to use only class definitions      bool        False
• func_defs  whether to use only function definitions   bool        False
• verbose    whether to log anything                    bool        False

positional arguments:
  src

options:
  -h, --help            show this help message and exit
  -m [MATCH ...], --match [MATCH ...]
  -d, --dry-run
  -l, --list
  -e, --escalate
  -c, --cls-defs
  -f, --func-defs
  -v, --verbose
```

## How it works

### The structure of a `mvdef` invocation

When you call `mvdef foo.py bar.py -d -c -m A`, equivalent to:

```sh
mvdef foo.py bar.py --dry-run --cls-defs --mv A
```

You're requesting to show the file diffs it'd take (`--dry-run`)
to move the class definition (`--cls-defs`) named `A` (`--mv A`)
from `foo.py` (the `src`, first positional argument)
to `bar.py` (the `dst`, second positional argument).

### Parsing the request

The request to move a definition is stored on a dataclass `mvdef.transfer.MvDef`
immediately upon invoking the program command.

Upon creation, this class stores 2 attributes `src_diff` and `dst_diff`
(both are `mvdef.diff.Differ` objects) which will coordinate the creation of patches,
or 'diffs'. These start their life with empty agendas (`mvdef.agenda.Agenda`).

Next, the main `MvDef` class calls its `check()` method, which returns an exception
(or raises it if `escalate` is True), preventing further work if the source file
does not contain a class named `A` as requested.

If the source file has the required definitions to fulfil the request,
then the `MvDef.diffs()` method gets called next,
populates the empty agendas on the `Differ` objects for the 2 files,
then produces the diffs they imply.

If the dry run setting is not used, the source and destination files are overwritten
with the changes, instead of just displaying the diffs.

### `lsdef` approach

`lsdef` is similar, but instead of making a `src_diff` it makes a `src_manifest`
(`mvdef.manifest.Manifest` object), and there is no `dst` file to handle.

Error handling is the same as above.

---

> _mvdef_ is available from [PyPI](https://pypi.org/project/mvdef), and
> the code is on [GitHub](https://github.com/lmmx/mvdef)
