# mvdef

Move function definitions from one file to another, moving or copying
associated import statements along with them.

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
