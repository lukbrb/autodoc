from dataclasses import dataclass
from functools import wraps
import inspect
import os
import reprlib
from typing import Any, Callable


@dataclass
class Argument:
    name: str
    annotation: Any
    value: Any


class Fonction:
    def __init__(self, py_function: Callable, args: tuple, kwargs: dict) -> None:
        self.fonction = py_function
        self.name = self.fonction.__name__
        # self.args = args
        # self.kwargs = kwargs
        self.arg_vals = list(args) + list(kwargs.values())
        self.docstring = inspect.getdoc(self.fonction)
        self.signature = inspect.signature(self.fonction)
        
        def _structure_args(self) -> list[Argument]:
                    """ Structure les tuple args et dico kwargs
            en une liste de `Argument`.
        """
        params = []
        for arg, argvalue in zip(self.signature.parameters.values(), self.arg_vals):
            params.append(Argument(arg.name, arg.annotation, argvalue))
        return params
    

def get_signature(func_name: str, all_args: dict[str, Any], return_val: Any) -> str:
    clsname = lambda x : type(x).__name__
    arguments = ", ".join(
        f"{arg_name}: {clsname(arg_val)}"
        for arg_name, arg_val in all_args.items()
    )
    arguments = arguments.rstrip(", ") # supprime la dernière virgule avant de refermer parenthèse
    return f"def {func_name}({arguments}) -> {clsname(return_val)}:\n"

def get_docstring(all_args: dict[str, Any], resultat: tuple[str, Any]):
    docstring = '\t"""\n\t:params:\n'
    for arg_name, arg_val in all_args.items():
        docstring += f"\t-{(arg_name)}: {reprlib.repr(arg_val)}\n"
    docstring += f'\n\t:returns: {resultat[0]}: {reprlib.repr(resultat[1])}\n\t"""\n\t...'
    return docstring

def autodoc(func):
    @wraps(func)  # If we want to chain decorators
    def wrapper(*args, **kwargs):
        resultat = func(*args, **kwargs)

        args_names = func.__code__.co_varnames[:len(args)]
        return_name = func.__code__.co_varnames[-1]
        func_name = func.__name__
        all_args = dict(zip(args_names, args))
        all_args |= kwargs
        def_filename = os.path.basename(func.__code__.co_filename) # with_csv_diff.py : filename où la fonction est définie
        signature = get_signature(func_name=func_name, all_args=all_args, return_val=resultat)
        docstring = get_docstring(all_args, resultat=(return_name, resultat))
        autostring = signature + docstring
        check_and_update_file(filename=f'{def_filename}i', file_content=autostring, function_name=func_name)
        return resultat

    return wrapper