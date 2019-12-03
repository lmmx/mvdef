from pathlib import Path
from mvdef import __path__ as module_dir, __package__ as module_name
from example import __path__ as example_dir
from src import __path__ as src_dir

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

try:
    assert len(src_dir) == 1
    src_dir = module_dir.parent / src_dir[0]
except AssertionError as e:
    raise NotImplementedError(e, "There should only be one src path here")

try:
    assert src_dir.exists() and src_dir.is_dir()
except AssertionError as e:
    raise ValueError(e, "src directory should be a directory that already exists")

# Exports:
#   - module_dir: absolute Path to the module directory, `mvdef/`,
#                 containing `__main__.py`, `src/`, and `example/`
#   - module_name: string giving the module name (`"mvdef"`)
#   - example_dir: absolute Path to the `example/` directory
#   - src_dir: absolute Path to the `src/` directory
