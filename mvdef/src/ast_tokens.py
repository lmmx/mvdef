from asttokens import ASTTokens
from ast import Import as IType, ImportFrom as IFType, walk

def get_imports(source_filepath, index_list=None):
    with open(source_filepath, 'r') as f:
        source = f.read()
    fl = source.split('\n')
    a = ASTTokens(source, parse=True)
    imports = [t for t in walk(a.tree) if type(t) in (IType, IFType)]
    if index_list is not None:
        imports = []
        for (n, n_i) in index_list:
            return [imports[i] for i in index_list]
    return imports

def count_imported_names(nodes):
    """
    Return an integer for a single node (0 if not an import statement),
    else return a list of integers for a list of AST nodes.
    """
    if type(nodes) is not list:
        if type(nodes) in [IType, IFType]:
            return len(nodes.names)
        else:
            assert ast.stmt in type(nodes).mro(), f"{nodes} is not an AST statement"
            return 0
    counts = []
    for node in nodes:
        if type(node) in [IType, IFType]:
            c = len(node.names)
            counts.append(c)
        else:
            assert ast.stmt in type(nodes).mro(), f"{nodes} is not an AST statement"
            counts.append(0)
    return counts

def locate_import_ends(source_filepath, index_list=None):
    ends = []
    nodes = get_imports(source_filepath, index_list)
    for n in nodes:
        end = {}
        end["line"], end["index"] = n.last_token.end[0]
        ends.append(end)
    return ends
