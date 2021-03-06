# mvdef

Package providing command line tools to move/copy Python functions/classes
and their associated import statements between files.

## Installation

To get the 4 `mvdef` tools on your command line, install from [PyPi](https://pypi.org/project/mvdef/)

```sh
pip install mvdef
```

All commands share identical usage syntax, but either move/copy the functions/classes indicated:

- `cpdef`
- `mvcls`
- `cpcls`

(Note that you may not mix and match these operations within a single call)

## Recipes

### Specifying what to move and where to move it to

`mvdef` is called on the command line with at the least an `-m` flag specifying the function to move (e.g. `foo`),
the file it's in (e.g. `src.py`) and the file to move it to (which will be created if it doesn't exist).

```sh
mvdef -m foo src.py dst.py
```

Additionally, `-i` specifies a 'path' to move the function into, e.g. within a class `Bar`:

```sh
mvdef -m foo -i Bar src.py dst.py
```

Some points to note about these flags:

- The `-m` flag can be repeated for as many functions as you want to move
- The `-i` flag is optional for any/every `-m` flag (but must come immediately after)
  - Without `-i`, the function named in `-m` will go in the global namespace (i.e. unindented)
    at the end of the file
- Both the `-m` and `-i` paths can have parts separated by:
  - `.` to indicate the method of a class
  - `:` to indicate the inner function of a function
  - `::` to indicate the inner class of a class
  - `:::` to indicate the higher order class of a function
    - (i.e. a class inside a funcdef, which I was advised might also be known as "a regret")

Additionally:

- The `-m`/`--mv` flags can go anywhere but I find it more natural to place them first,
  so the command reads "move {this function} from {this file} to {this file}")
- If you move the last item out of a funcdef or class, `mvdef` will automatically
  repair it so it's still valid Python by replacing the excised lines with a `pass` statement

Still hungry? See the [cookbook](#cookbook) below!

## Usage

Run `mvdef -h` to get this reminder:

```
usage: mvdef [-h] [-m MV] [-i INTO] [-v] [-b] [-d] src dst

Move function definitions and associated import statements from one file to another within a
library.

positional arguments:
  src
  dst

optional arguments:
  -h, --help            show this help message and exit
  -m MV, --mv MV
  -i INTO, --into INTO
  -v, --verbose
  -b, --backup
  -d, --dry-run
```

- For development flags not shown above (`--debug`, `--show-tracebacks`, `--demo`) see
  [below](#Development_flags)

### Cookbook

If you're curious to try this out but don't want to dive straight in, below are some
more examples for the careful.

#### A cautious check before moving

```sh
mvdef -m myfunc src.py dst.py -vd
```

- `-v` is "verbose": print out the import statement edits to be made and functions to move
- `-d` is "dry run": don't edit any files, just prepare as if you were about to
  - It's not possible to run a dry run without a report, `mvdef` will tell you it has "nothing to do"

This is handy to check that there are no errors in the specified move,
i.e. that the move will be possible (for example that you didn't make typos in any names),
and will give a printout of what import statements will change in each file edited (if any).

#### A safeguarded move

```sh
mvdef -m myfunc src.py dst.py -vb
```

- `-v`: "verbose" (as above, print out import statement edits and funcdefs to move)
- `-b`: "backup", make backups (not overwriting prior ones, as `.backup`, then `.backup0`, etc)
  - `src.py` --> `.src.py.backup`
  - `dst.py` --> `.dst.py.backup`

#### A simple move with a specified target

```sh
mvdef -m foo -i Bar src.py dst.py
```

This moves the lines of the funcdef `foo` from `src.py` to the end of the classdef `Bar`
(and note that this will indent the lines of `foo` by 4 spaces).

#### Moving methods between classes

```sh
mvdef -m A.__init__ -i B src.py dst.py
```

will move the method `__init__` from the class `A` in `src.py` into the class `B` in `dst.py`

- Note that unlike the Unix tools `mv` and `cp`, the `mvdef` tools do not overwrite a function
  if it already exists, so if the class `B` already has an `__init__` function it will simply
  end up with 2 `__init__` functions, its original will not be overwritten.
- Additionally, the default position for newly moved (or copied) defs is at the end of the AST
  node (or the end of the namespace if no `-i`/`--into` node is specified), so in the case that
  the destination namespace ends up with duplicates, e.g. the `B` class with 2 `__init__` functions,
  the newly moved one would "act last" i.e. it would take priority when instantiating the class,
  as of course the latest definition overwrites any earlier definition of the same ID.


#### Multiple moves

```sh
mvdef -m hello -i Bar.foo -m baz -i Bax src.py dst.py
```

will move:

- the funcdef `hello` from the global namespace of `src.py` into the method
  `foo` of the class `Bar` in `dst.py` (making it an inner function of the method)
- the funcdef `baz` from the global namespace of `src.py` into the class `Bax`
  in `dst.py` (making it a method of the class)

#### Coming soon

Paths to `-mv`/`--mv` and `-i`/`--into` will soon support:

- **decorators**: to indicate a particular version of funcdefs with identical names
  - e.g. for `property` decorators which have a `@property` and a `@foo.setter` variant
  - see [#10](https://github.com/lmmx/mvdef/issues/10)
- **wildcards**: to avoid having to specify a full path to a particular function
  - e.g. `-m **foo`
  - see [#28](https://github.com/lmmx/mvdef/issues/28)
  
#### Moving with imports: a simple case study

Consider the file `hello.py`:

```py
from pprint import pprint

def hello():
    pprint("hi")
```

To move the `hello` funcdef to the blank file `world.py`, we run:

```sh
mvdef -m hello hello.py world.py -v
```
⇣
```STDOUT
--------------RUNNING mvdef.cli⠶main()--------------
• Determining edit agenda for hello.py:
 ⇢ MOVE  ⇢ (import 0:0 on line 1) pprint ⇒ <pprint.pprint>
⇒ Functions moving from /home/ubuntu/stuff/simple_with_import_edit/hello.py: ['hello']
• Determining edit agenda for world.py:
 ⇢ TAKE  ⇢ (import 0:0 on line 1) pprint ⇒ <pprint.pprint>
⇒ Functions will move to /home/ubuntu/stuff/simple_with_import_edit/world.py
------------------COMPLETE--------------------------
```

## New features

Check out the releases and changelogs in full [on GitHub](https://github.com/lmmx/mvdef/tags)

### Development flags

#### `--debug`

When you want to debug why something works or why it didn't work, change the `mvdef -m ...`
command to `python -im mvdef -m ...` to gain an interactive shell after the command runs.
If you supply `--debug` at the end of this command, the variable `link` will be populated
with the `FileLink` instance which can be inspected and debugged (without need for `pdb`).

#### `-show-tracebacks`

By default, `mvdef` will curtail the stack trace when raising an error
(as [robust interfaces are more user-friendly](https://clig.dev/#robustness-principle)).

To print the full stack trace, add the `--show-tracebacks` flag (and submit errors you find
[on GitHub](https://github.com/lmmx/mvdef/issues/new)).

#### `--demo`

To run a built-in demo, run `mvdef --demo` (equivalent to running the following within the
package source):

```sh
mvdef -m pprint_dict mvdef/example/demo_program.py mvdef/example/new_file.py -vd
```

- The function `pprint_dict` is moved from the source file to the
  destination file, taking along import statements (or more precisely,
  taking individual aliases from import statements, which then form new import statements
  in the destination file). The top right of the image displays a report of the 'agenda'
  which `mvdef` follows, alias by alias, to carry out these changes.
- This demo can be reproduced by running `python -im mvdef --demo` from the main directory
  upon cloning this repository, and inspecting the source file (`demo_program.py`) and
  destination file (`new_file.py`) under `mvdef/example/`.
- This demo creates hidden `.backup` files, which can be used to 'reset' the demo by
  moving them back so as to overwrite the original files.


`mvdef --demo` will display a (dry run) demo of the output from moving a function from
one file to another (in colour in the terminal, using ANSI codes):

```STDOUT
--------------RUNNING mvdef.demo⠶main()--------------
{'foo': 1, 'bar': 2}
hello//human, welcome to spin.systems
✔ All tests pass
• Determining edit agenda for demo_program.py:
 ⇢ MOVE  ⇢ (import 0:0 on line 1) ft ⇒ <functools>
 ⇢ MOVE  ⇢ (import 1:0 on line 2) pprint ⇒ <pprint.pprint>
 ⇢ MOVE  ⇢ (import 1:1 on line 2) pformat ⇒ <pprint.pformat>
⇠  KEEP ⇠  (import 3:1 on line 4) pathsep ⇒ <os.path.sep>
⇠  KEEP ⇠  (import 2:0 on line 3) req ⇒ <urllib.request>
 ✘ LOSE ✘  (import 3:0 on line 4) bname ⇒ <os.path.basename>
 ✘ LOSE ✘  (import 3:2 on line 4) islink ⇒ <os.path.islink>
⇒ Functions moving from /home/louis/dev/mvdef/src/mvdef/example/demo_program.py: ['pprint_dict']
• Determining edit agenda for new_file.py:
 ⇢ TAKE  ⇢ (import 0:0 on line 1) ft ⇒ <functools>
 ⇢ TAKE  ⇢ (import 1:0 on line 2) pprint ⇒ <pprint.pprint>
 ⇢ TAKE  ⇢ (import 1:1 on line 2) pformat ⇒ <pprint.pformat>
⇒ Functions will move to /home/louis/dev/mvdef/src/mvdef/example/new_file.py
DRY RUN: No files have been modified, skipping tests.
------------------COMPLETE--------------------------
```

## Motivation

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

## TODO

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
