# mvdef

# Summary

Move function definitions from one file to another, moving or copying
associated import statements along with them.

# Motivation

My workflow typically involves a process of starting to work in one file,
with one big function, and later breaking out that function into smaller functions
once I've confirmed the necessary control flow organisation (determined the
general regions which operate on the same values, and so on).

After 'breaking out' the code into multiple smaller functions in this way,
it'll often be the case that some of the functions are thematically linked
(e.g. they operate on the same type of variable or are connected in the workflow).
In these cases, it's useful to move these functions out of the original file,
and into a module file together, then import their names back into the original file
if or as needed.

The problem comes from then having to do the mental calculation (and often old
fashioned searching for library-imported names within the file) of whether the
functions I am trying to move out into another file rely on import statements,
and whether there are other functions which also rely on the same imported names.
If I guess and get it wrong, I may then have to run the code multiple times and
inspect the error message tracebacks until I figure out the full set, or else
just reset it to where I was, in which case the time spent so far was wasted!

All of this motivates a library which can handle such operations for me, if not
because I have difficulty so much as it is a waste of time every time, which
also interrupts the train of thought (increasingly so as the software gets more
complex, with more functions and libraries to consider).

Software can scale to handle these higher levels of complexity no differently than
it can handle a simple case, and I began writing this on the basis that "if I'm going
to figure it out for this one instance, I may as well code it for any instance going
forward".

# Approach

The idea is to run a command like `mvdef src.py dst.py fn1 fn2 fn3` to do the following:

1) Back up `src.py` and `dst.py`, as `src.py.backup` and `dst.py.backup` in case it doesn't work
2) Optional: Define some test that should pass after the refactor, when `src.py` imports `fn1, fn2, fn3` from `dst.py`
   - If not, it would just be a matter of testing this manually
3) Enumerate all import statements in `src.py` (nodes in the AST of type `ast.Import`)
4) Enumerate all function definitions in `src.py` (nodes in the AST of type `ast.FunctionDef`)
5) Find the following subsets:
   - `mvdefs`: subset of all function definitions which are to be moved (`fn1`, `fn2`, `fn3`)
   - `nonmvdefs`: subset of all function definitions which are not to be moved (not in `mvdefs`)
   - `mvdef_imports`: Import statements used by the functions in `mvdefs`
   - `nonmv_imports`: Import statements used by the functions in `nonmvdefs`
6) Move the import statements in only `mvdef_imports`
7) Copy the import statements in both `mvdef_imports` and `nonmv_imports`
8) ...and only then move the function definitions across
9) If tests were defined in step 2, check that these tests run
   - If they fail, restore the backup and give the altered src/dst `.py` files `.py.mvdef_fix` suffixes
