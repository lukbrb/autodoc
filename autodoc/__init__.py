from functools import wraps
from .core import Autodoc
from .utils import check_and_update_file

def autodoc(func):
    @wraps(func)  # If we want to chain decorators
    def wrapper(*args, **kwargs):
        resultat = func(*args, **kwargs)

        fulldoc = Autodoc(func, args, kwargs, resultat)
        check_and_update_file(filepath=f"{fulldoc.filename}i", file_content=fulldoc.generate_imports(), function_name="IMPORTS")  # Note: pas besoin de l'arg function_name pour écrire les imports.
        check_and_update_file(filepath=f'{fulldoc.filename}i', file_content=fulldoc.generate_full_doc(), function_name=fulldoc.funcname)
        return resultat
    return wrapper
