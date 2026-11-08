import ast


def extract(text: str) -> list[dict]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines = text.splitlines()
    result = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            doc = ast.get_docstring(node) or ""
            start = min([node.lineno] + [d.lineno for d in node.decorator_list])
            result.append(
                dict(
                    name=node.name,
                    kind=type(node).__name__,
                    signature=lines[node.lineno - 1].strip()[:180],
                    start_line=start,
                    end_line=node.end_lineno,
                    docstring_first_line=doc.splitlines()[0] if doc else "",
                )
            )
    return sorted(result, key=lambda s: s["start_line"])
