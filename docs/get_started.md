---
title: Get Started
icon: material/human-greeting
---

# Getting started

## 1. Installation

Mvdef is available on PyPi:

```bash
pip install mvdef
```

## 2. Usage

You can use mvdef on the command line:

=== "Code"

    ```bash
    mvdef -h
    ```

=== "Output"

    ```bash
    usage: mvdef [-h] -m [MV ...] [-d] [-e] [-c] [-f] [-v] [--version] src dst
    
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
      --version             show program's version number and exit
    ```

## 3. Local development

- To set up pre-commit hooks (to keep the CI bot happy) run `pre-commit install-hooks` so all git
  commits trigger the pre-commit checks. I use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).
  This runs `black`, `flake8`, `autopep8`, `pyupgrade`, etc.

- To set up a dev env, I first create a new conda environment and use it in PDM with `which python > .pdm-python`.
  To use `virtualenv` environment instead of conda, skip that. Run `pdm install` and a `.venv` will be created if no
  Python binary path is found in `.pdm-python`.

- To run tests, run `pdm run python -m pytest` and the PDM environment will be used to run the test suite.

## 4. Acknowledgements

Mvdef was developed by [@permutans](https://twitter.com/permutans).
