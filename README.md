# mvdef

# Summary

Move function definitions from one file to another, moving or copying
associated import statements along with them.

# Installation

mvdef is [available on PyPi](https://pypi.org/project/mvdef/): install it
using `pip install mvdef`

After installing to your environment from PyPi, the `mvdef` command will be available
on the command line. Type `mvdef -h` to get the following usage message.

# Usage

```
usage: mvdef [-h] [--demo] [-m MVDEF] [--src SRC] [--dst DST] [-r] [-b] [-d]

optional arguments:
  -h, --help            show this help message and exit
  --demo
  -m MVDEF, --mvdef MVDEF
  --src SRC
  --dst DST
  -r, --report
  -b, --backup
  -d, --dry-run
```

## Example usage

`mvdef -m func1 --src path/to/source_program.py --dst path/to/destination_program.py -rb`

will move the funcdef named `func1` from `source_program.py` to `destination_program.py`,
while reporting output (thanks to the `-r` flag) and making backups (thanks to the `-b` flag).

- Further functions can be moved by adding more `-m` flags each followed by a function name,
e.g. `mvdef -m func1 -m func2 -m func3` ...

For instance to carry out the demo from the command line, run `mvdef --demo`, or equivalently:

`mvdef -m show_line --src mvdef/example/demo_program.py --dst mvdef/example/new_file.py -rb`

If you feel like there would be a more concise or useful way of specifying command line
arguments, please let me know by making a GitHub issue, however I chose not to just have
anonymous parameters as over time it could get easy to forget which are which.

# Motivation

My workflow typically involves a process of starting to work in one file,
with one big function, and later **breaking out** that function into smaller
functions once I've settled on the first draft of control flow organisation.

After 'breaking out' the code into multiple smaller functions in this way,
it'll often be the case that some of the functions are thematically linked
(e.g. they operate on the same type of variable or are connected in the workflow).
In these cases, it's useful to **move function definitions out of the main file**,
and into a module file together, then import their names back into the main file
if or as needed.

- If I have two functions `A` and `B`, and my file calculates `A() + B()`, not only
  can I move `A` and `B` into some other module file `mymodule`, but I can put a
  wrapper function `C` in it too, and reduce the number of names I import
  ```py
  def C():
      ans = A() + B()
      return ans
  ```
  both saving on the complexity in the main file, and giving 'more space' to focus
  on `A`, `B` and `C` separate from the complexity of what's going on in the main file
  (which in turn makes theme-focused tasks like documentation more straightforward).

The problem comes from then having to do the mental calculation (and often old
fashioned searching for library-imported names within the file) of whether the
functions I am trying to move out into another file rely on names that came from
import statements, and if so, **whether there are other functions which also rely on
the same imported names.** If I guess and get it wrong, I may then have to run the
code multiple times and inspect the error message tracebacks until I figure out
the full set, or else just reset it to where I was if things get particularly
messy, in which case the time spent trying to move functions and import statements
manually was wasted.

All of this motivates a library which can handle such operations for me, not just
because it requires some thought to do manually so much as that it's a **waste of
development time**, and what's more it interrupts the train of thought (increasingly
so as the software gets more complex, with more functions and libraries to consider).

Software can scale to handle these higher levels of complexity no differently than
it can handle a simple case, and I began writing this on the basis that "if I'm going
to figure it out for this one instance, I may as well code it for any instance going
forward".

# Demo

![](mvdef/example/documentation/demo-success-screenshot-annotated.png)

- **Above:** the function `show_line` is moved from the source file (_left_) to the
  destination file (_right_), taking along import statements (or more precisely,
  taking individual aliases from import statements, which then form new import statements
  in the destination file). The top right of the image displays a report of the 'agenda'
  which `mvdef` follows, alias by alias, to carry out these changes.
- This demo can be reproduced by running `python -im mvdef --demo` from the main directory
  upon cloning this repository, and inspecting the source file (`demo_program.py`) and
  destination file (`new_file.py`) under `mvdef/example/`.
- This demo creates hidden `.backup` files, which can be used to 'reset' the demo by
  moving them back so as to overwrite the original files.

# Project status and future plans

- November 2019: This library is currently working only as a proof of concept, with a demo, and not
yet working for code.
- December 2019: The demo now works, and using the command line flags it works as a command line tool
for any list of functions and any pair of files specified.

I'd like this to end up being a command line tool that assists the development workflow
similar to how [`black`](https://github.com/psf/black/) has simplified linting to best
practice conventions for Python code style, as a tool callable on a Python file to
change it in place, and reliable enough to trust it not mess up any of your files in
the process.

# Changelog

- version 0.1.7:
  - resolved a bug arising from `mvdef.src.ast_util`⠶`get_def_names` not registering variables assigned
  implicitly via for loops and list comprehensions ([issue #2](/issues/2))

# Approach

The idea is to run a command like `mvdef src.py dst.py fn1 fn2 fn3` to do the following:

- [x] Back up `src.py` and `dst.py`, as `src.py.backup` and `dst.py.backup` in case it doesn't work
   - [x] Function completed in `src.backup`⠶`backup()` with `dry_run` parameter, called in `src.demo`
   - [ ] I'd also like to add the option to rename functions, using a pattern or list to rename
     as
     - [ ] `src.rename` not yet implemented
- [x] Optional: Define some test that should pass after the refactor,
  when `src.py` imports `fn1, fn2, fn3` from `dst.py`
   - [x] Tests defined for all functions in `example.demo_program` in `example.test`⠶`test_report`,
     called in `__main__`
     - [x] Tests are checked and raise a `RuntimeError` if they fail at this
       stage (i.e. the whole process aborts before any files are modified or created)
   - If not, it would just be a matter of testing this manually (i.e. not necessary to define test
     to use tool, but suggested best practice)
- [x] Enumerate all import statements in `src.py` (nodes in the AST of type `ast.Import`)
   - `src.ast_util`⠶`annotate_imports` returns this list, which gets assigned to `imports`
     in `src.ast_util`⠶`parse_mv_funcs`
- [x] Enumerate all function definitions in `src.py` (nodes in the AST of type `ast.FunctionDef`)
   - `ast`⠶`parse` provides this as the `.body` nodes which are of type `ast.FunctionDef`.
     - This subset of AST nodes is assigned to `defs` in `src.ast_util`⠶`ast_parse`.
- [x] Find the following subsets:
   - [x] `mvdefs`: subset of all function definitions which are to be moved (`fn1`, `fn2`, `fn3`)
     - This subset is determined by cross-referencing the names of the `defs` (from previous step)
       against the `mvdefs` (list of functions to move, such as `["fn1", "fn2", "fn3"]`),
       in the dedicated function `src.ast_util`⠶`get_def_names`, then returned by `src.ast_tools`⠶
       `parse_mv_funcs` as a list, assigned to `mvdefs` in `src.ast_util`⠶`ast_parse`.
   - [x] `nonmvdefs`: subset of all function definitions **not** to be moved (not in `mvdefs`)
     - This subset is determined by negative cross-ref. to names of the `defs` against the
       `mvdefs` (such as `["fn4", "fn5", "fn6"]`), again using `src.ast_util`⠶`get_def_names`,
       then returned by `src.ast_util`⠶`parse_mv_funcs` as a list, assigned to `nonmvdefs`
       in `src.ast_util`⠶`ast_parse`.
   - [x] `mv_imports`: Import statements used only by the functions in `mvdefs`
   - [x] `nonmv_imports`: Import statements used only by the functions in `nonmvdefs`
   - [x] `mutual_imports`: Import statements used by both functions in `mvdefs` and `nonmvdefs`
   - [x] `nondef_imports`: Import statements not used by any function
     - Note that these may no longer be in use, but this can only be confirmed by checking
       outside of function definitions too.
     - [ ] Potentially add this feature later, for now just report which imports aren't used.
- Handle the 3 types of imported names:
  - [x] **Move** the import statements in `mv_imports` (received as "take")
  - [x] **Keep** the import statements in `nonmvdef_imports`
  - [x] **Copy** the import statements in `mutual_imports` (received as "echo")
- ...and also:
  - [x] Handle moving one import name from an import statement importing multiple
        names (i.e. where you can't simply copy the line)
  - [x] Handle multi-line imports (i.e. where you can't simply find the names on one line)
  - [x] ...and remove unused import statements (neither in/outside any function definitions)
- ...and only then move the function definitions in `mvdefs` across
- [x] If tests were defined in step 2, check that these tests run
   - [x] For the demo, the tests are checked (by running `test_report` a 2nd time) after
     `src.demo`⠶`run_demo` has returned a parsed version of the source and destination files
     (which will only matter once the parameter `nochange` is set to `False` in `run_demo`,
     allowing it to propagate through the call to `src.demo`⠶`parse_example` into a call to
     `src.ast_util`⠶`ast_parse(..., edit=True)` and ultimately carry out in-place editing of the
     source and/or destination file/s as required).
   - [ ] If they fail, ask to restore the backup and give the altered src/dst `.py` files
     `.py.mvdef_fix` suffixes (i.e. always permit the user to exit gracefully with no further
     changes to files rather than forcing them to)
