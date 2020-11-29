from pathlib import Path
from .example import __path__ as example_dir
from . import __path__ as module_dir, __package__ as module_name

try:
    assert len(module_dir) == 1
    module_dir = Path(module_dir[0])
except AssertionError as e:
    raise NotImplementedError(e, "There should only be one module directory here")

try:
    assert module_dir.exists() and module_dir.is_dir()
except AssertionError as e:
    raise ValueError(e, "Module directory should be a directory that already exists")

try:
    assert module_dir.name == module_name
except AssertionError as e:
    raise ValueError(e, "Module directory name doesn't match record of module name")

try:
    assert len(example_dir) == 1
    example_dir = module_dir.parent / example_dir[0]
except AssertionError as e:
    raise NotImplementedError(e, "There should only be one example path here")

try:
    assert example_dir.exists() and example_dir.is_dir()
except AssertionError as e:
    raise ValueError(e, "Example directory should be a directory that already exists")

# Exports: (note: the module_dir and src_dir might need switching after renaming?)
#   - module_dir: absolute Path to the module directory, `src/`,
#                 containing `__main__.py`, `mvdef/`, and `example/`
#   - module_name: string giving the module name (`"mvdef"`)
#   - example_dir: absolute Path to the `example/` directory
