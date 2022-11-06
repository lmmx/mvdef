# TODO list

## Change default action from listing definitions to fixing `__all__`

(Initial title: "`-f`/`--fix` flag (or `-f`/`--fix`")

The ability to create `__all__` assignment lines for comparison is great,
but it'd be preferable to edit (or "fix") an existing assignment, or add it if it's missing.
This would default to both classdefs and funcdefs (for simplicity).

In fact, it'd be preferable to make all of the tools default to all definitions, and specify
`-f`/`--funcdefs` or `-c`/`--classdefs` to narrow the type of definition.

(Entrypoints for `mvcls` and `mvfunc` entrypoints could also be used to override these)

If `-f` would be used for `--funcdefs` then `-f` couldn't be used for `--fix` in the `lsdef` CLI.

Instead, the default behaviour could be to overwrite,
with `-d`/`--dry-run` flag simulating the diff (as for `mvdef`/`cpdef`.

This would entail:

- adding the `-d`/`--dry-run` flag to the `LsDef` dataclass, and using it to control diff generation
- removing the `-p`/`--pprint` flag (the diff from using `-d` gives an equivalent/superior output)
- changing the `-l`/`--ls` flag to `-m`/`--match`, emphasising that it matches a regex (for now just `*`)
- making an `-l`/`--list` flag for what is the current behaviour

There is surely an optimal order to carry out these 4 steps in.

- One objective is to minimise disruption (i.e. the period of redevelopment in which tests/the tool itself will be broken).
- Another is to follow the natural or 'golden' path.

To see this 'golden path it'd help to identify connections between the 4 steps, how they form a network.

The steps again in brief are:

- add `--dry-run`
- remove `--pprint`
- rename `--ls` to `--match`
- add `--list`

Renaming `ls` to `match` has no side effects, and is a prerequisite for adding `list`, so:

The other 2 are really a sort of renaming with added functionality: if we see it as such,
then we'd be able to touch all the same parts (making it more likely to succeed first try).
For now then, we can say that `dry_run` is the 'new name' for `pprint`, and add the specific
functionality after the renaming.

Since renaming flags is best done all at once, I'll do the `pprint` renaming second (which is a bit
counter-intuitive, but means I don't have to think about the CLI interface after these initial steps).

1. rename `--ls` to `--match`
2. rename `--pprint` to `--dry-run`
3. add `--list`
4. add `--dry-run` diff functionality

After this, the functionality would be lacking, but tests would be passing so building the new
functionality would have a strong base to begin from.

Also note that the other commands would change to default to `all_defs` (meaning cls or funcdefs)
leaving the `-a` flag available for use as control for a feature for `__all__` generation.
We could pass `-a` to modify or update the `__all__` variable in accordance with the removed/added
definitions (as already done for imports).

**Progress:**

- [x] rename `--ls` to `--match`
  - `LsDef` dataclass attribs: `ls` -> `match`
  - `Manifest` dataclass attribs: `ls` -> `matchers`
  - Tests passed
- [x] rename `pprint` to `--dry-run`
- [x] add `--list`
  - Added to help message, test passed
  - TODO: replace the current functionality
- [ ] make `--dry-run` produce a diff of what it would edit
  - TODO: integrate the `Manifest` class into `Differ`
- [ ] update other commands with `-a` to mean `all` as in `__all__` and default to all defs
- [ ] write tests for dry run diffs on `one_func_all` and `many_func_all`

The `LsDef` mover class differs from the other 2 in that it uses a `Manifest`
object where they use `Differ`. Since we will now in fact be creating diffs,
we want to use a `Differ` too! This potentially simplifies things.

To assist with the class editing I'm preparing to carry out,
I am simplifying the (currently somewhat ad-hoc) provision of kwargs
to the `Checker` and `Differ` classes,
by OOP methods that can be inherited or overridden in subclasses.
This moves code complexity away from the business logic, into the base class.

## Multiple imports

Currently due to how import moving was implemented,
if there are N imports on a line, the line is copied N times!
This is OK for me (for now) since I use an `isort` ALE linter that
immediately fixes them.

## ALE integration

The vim editor ALE lets you run 'fixers' on your code upon saving.

If the default action of lsdef is changed from sending a list to STDOUT,
to instead update the `__all__` of a file to sync it with its definitions,
this make it a viable fixer.

## `-r`/`--retain` and `-i`/`--import-style` flags

When moving, we may want to retain a reference to the definition that was moved out.

For this, we could either use:

- Absolute imports with no known parent package, e.g. `from transfer import MvDef`
- Package-relative imports, e.g. `from .transfer import MvDef` (within a package)
- Absolute package imports, e.g. `from mvdef.transfer import MvDef`

We already have a means to inject imports into the file, the challenge would be
in reliably detecting the parent package (personally I prefer package-relative imports,
but there's a time and a place for each of the 3 types).

The `-i`/`--import-style` flag could take a string with the following options:

- `.` would use package-relative imports (default behaviour)
- `a` would use absolute imports, regardless of whether a parent package is found
- `p` would use absolute package imports

When no parent package is found, `.` and `p` would fall back to `a`.

## Multi-level definition spec

The `lsdef` tool currently has a hardcoded filter for "depth 1" nodes in the AST,
i.e. top level classdefs and funcdefs in a module, with the defline 0-indented
and the body indented by one level (4 spaces).

This makes sense as the `ls` value is hardcoded as `*` which in Unix indicates
an immediate path. This could be extended to specific paths such as:

- `.*`
- `..*`
