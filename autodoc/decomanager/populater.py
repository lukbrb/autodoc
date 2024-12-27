import argparse
import os
import ast
import astor
from .conf import exclude_dirs, exclude_func, exclude_mods
decorator_to_add = 'autodoc'
import_to_add = ''


def add_decorator_to_functions(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    tree = ast.parse(file_content)


    class DecoratorAdder(ast.NodeTransformer):

        def visit_FunctionDef(self, node):
            if node.name not in exclude_func:
                node.decorator_list.insert(0, ast.Name(id=decorator_to_add,
                    ctx=ast.Load()))
            return node
    tree = DecoratorAdder().visit(tree)
    ast.fix_missing_locations(tree)
    modified_content = astor.to_source(tree)
    if import_to_add not in modified_content:
        modified_content = import_to_add + '\n\n' + modified_content
    with open(file_path, 'w') as file:
        file.write(modified_content)


def process_directory(directory_path):
    for root, _, files in os.walk(directory_path):
        if root not in exclude_dirs:
            for file in files:
                if file.endswith('.py') and file not in exclude_mods:
                    file_path = os.path.join(root, file)
                    add_decorator_to_functions(file_path)


def main():
    parser = argparse.ArgumentParser(description=
        'Process directory to remove decorators.')
    parser.add_argument('--dir', required=True, help='Directory to process')
    args = parser.parse_args()
    process_directory(args.dir)


if __name__ == '__main__':
    main()
    