import argparse
import os
import ast
import astor
from .conf import exclude_dirs, exclude_func, exclude_mods
decorator_to_remove = 'autodoc'
import_to_remove = ''


def remove_decorator_from_functions(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    tree = ast.parse(file_content)


    class DecoratorRemover(ast.NodeTransformer):

        def visit_FunctionDef(self, node):
            if node.name not in exclude_func:
                node.decorator_list = [decorator for decorator in node.
                    decorator_list if not (isinstance(decorator, ast.Name) and
                    decorator.id == decorator_to_remove)]
            return node
    tree = DecoratorRemover().visit(tree)
    ast.fix_missing_locations(tree)
    modified_content = astor.to_source(tree)
    if import_to_remove in modified_content:
        modified_content = modified_content.replace(import_to_remove, ''
            ).strip()
    with open(file_path, 'w') as file:
        file.write(modified_content)


def process_directory(directory_path):
    for root, _, files in os.walk(directory_path):
        if root not in exclude_dirs:
            for file in files:
                if file.endswith('.py') and file not in exclude_mods:
                    file_path = os.path.join(root, file)
                    remove_decorator_from_functions(file_path)


def main():
    parser = argparse.ArgumentParser(description=
        'Process directory to remove decorators.')
    parser.add_argument('--dir', required=True, help='Directory to process')
    args = parser.parse_args()
    process_directory(args.dir)


if __name__ == '__main__':
    main()
    