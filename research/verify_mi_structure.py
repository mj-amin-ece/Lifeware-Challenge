"""Verify original callable bodies and literal constants through their public imports.

--baseline points to the committed my_solution source tree. Function docstrings
and source locations may change; executable ASTs, signatures and decorators must
stay identical. Moved inherited methods are checked through their original class.
"""
import argparse
import ast
import copy
import importlib
import inspect
import pathlib
import sys
import textwrap


class WithoutDocs(ast.NodeTransformer):
    def generic_visit(self, node):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if node.body and isinstance(node.body[0], ast.Expr):
                value = node.body[0].value
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    node.body = node.body[1:]
        return super().generic_visit(node)


def executable(node):
    return ast.dump(WithoutDocs().visit(copy.deepcopy(node)), include_attributes=False)


def check_function(original, current, label):
    source = textwrap.dedent(inspect.getsource(inspect.unwrap(current)))
    actual = ast.parse(source).body[0]
    assert executable(original) == executable(actual), f'Executable body/signature changed: {label}'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=pathlib.Path, required=True)
    parser.add_argument('--solution', type=pathlib.Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.solution.resolve()))
    functions = constants = 0
    for path in sorted(args.baseline.rglob('*.py')):
        relative = path.relative_to(args.baseline)
        name = '.'.join(relative.with_suffix('').parts)
        module = importlib.import_module(name)
        for node in ast.parse(path.read_text()).body:
            if isinstance(node, ast.FunctionDef):
                check_function(node, getattr(module, node.name), f'{name}.{node.name}')
                functions += 1
            elif isinstance(node, ast.ClassDef):
                current_class = getattr(module, node.name)
                for method in node.body:
                    if isinstance(method, ast.FunctionDef):
                        check_function(method, getattr(current_class, method.name),
                                       f'{name}.{node.name}.{method.name}')
                        functions += 1
            elif isinstance(node, ast.Assign):
                try:
                    value = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assert getattr(module, target.id) == value, f'Constant changed: {name}.{target.id}'
                        constants += 1
                    elif isinstance(target, ast.Tuple):
                        for field, expected in zip(target.elts, value, strict=True):
                            assert getattr(module, field.id) == expected, f'Constant changed: {name}.{field.id}'
                            constants += 1
    print(f'PASS: {functions} original callable ASTs, signatures and decorators are identical through public imports')
    print(f'PASS: {constants} original literal constants retain their values and public imports')


if __name__ == '__main__':
    main()
