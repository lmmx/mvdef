# mvdef

[![Documentation](https://readthedocs.org/projects/mvdef/badge/?version=latest)](https://mvdef.readthedocs.io/en/latest/)
[![CI Status](https://github.com/lmmx/mvdef/actions/workflows/master.yml/badge.svg)](https://github.com/lmmx/mvdef/actions/workflows/master.yml)
[![Coverage](https://codecov.io/gh/lmmx/mvdef/branch/master/graph/badge.svg)](https://codecov.io/github/lmmx/mvdef)
[![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Package providing command line tools to move/copy function/classes and their associated import statements between files

[Read The Docs](https://mvdef.readthedocs.io/en/latest/)

## Requires

- Python 3.9+

## Installation

```sh
pip install mvdef
```

## Usage

```
usage: mvdef [-h] -m [MV ...] [-d] [-e] [-v] src dst

  Move function definitions from one file to another, moving/copying
  associated import statements along with them.

  Option     Description                                Type (default)
  —————————— —————————————————————————————————————————— ——————————————
• src        source file to take definitions from       Path
• dst        destination file (may not exist)           Path
• mv         names to move from the source file         list of str
• dry_run    whether to only preview the change diffs   bool (False)
• escalate   whether to raise an error upon failure     bool (False)
• verbose    whether to log anything                    bool (False)

positional arguments:
  src
  dst

options:
  -h, --help            show this help message and exit
  -m [MV ...], --mv [MV ...]
  -d, --dry-run
  -e, --escalate
  -v, --verbose
```

> _mvdef_ is available from [PyPI](https://pypi.org/project/mvdef), and
> the code is on [GitHub](https://github.com/lmmx/mvdef)
