# flake8: noqa
from ast import ClassDef, FunctionDef
from functools import partial

__all__ = ["_find_node", "_find_def", "_find_cls"]

### Helper functions used for finding the node given a path within `set_defs_to_move`
def _name_check(node, name):
    "Check whether an AST `node`’s `.name` attribute is `name`"
    return node.name == name


def _catch_next(iterable):
    try:
        return next(iterable)
    except StopIteration:
        return None


def _find_node(nodes, name):
    "Return the first node in `nodes` whose `.name` attribute is `name`"
    p_name_check = partial(_name_check, name=name)
    it = filter(p_name_check, nodes)
    val = _catch_next(it)
    return val


def _find_def(node, name):
    """
    Return the first `ast.FunctionDef` subnode in the body of `nodes` whose `.name`
    attribute is `name`
    """
    def_nodes = [n for n in node.body if type(n) is FunctionDef]
    return _find_node(def_nodes, name)


def _find_cls(node, name):
    """
    Return the first `ast.ClassDef` subnode in the body of `nodes` whose `.name`
    attribute is `name`
    """
    cls_nodes = [n for n in node.body if type(n) is ClassDef]
    return _find_node(cls_nodes, name)
