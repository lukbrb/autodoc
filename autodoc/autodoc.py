""" Ce module a pour but de créer dynamiquement des fichiers d'interface lorsque le code est lancé.
    Utilisation :
    - Le module s'utilise comme décorateur :
    `monmodule.py`
    |_> @autodoc
    |_> def ma_func(arg1, arg2):
            ...
    
    Le résultat est écrit dans un fichier d'interface `.pyi`
    >>> `monmodule.pyi`
        |_> def ma_func(arg1: <type(arg1)>, arg2: <type(arg2)) -> type[return de `ma_func`]
        ''' 
            - arg1 : type(arg1) :: extrait(arg1)
            - arg2 : type(arg2) :: extrait(arg2)

        return : 
            - returnvar : extrait(arg2)

        Exemple : 
            `ma_func(extrait(arg1), extrait(arg2))`
            >>> extrait(returnvar)
        '''   
            ...
"""

from dataclasses import dataclass
import inspect
import logging
import os
import reprlib
from pathlib import Path
from functools import wraps
from typing import Any, Callable, Iterable
from inspect import Signature, Parameter

def check_and_update_file(filename: str, file_content: str, function_name: str) -> None:
    typings_dir = Path('typings')
    typings_dir.mkdir(parents=True, exist_ok=True)

    file_path = typings_dir / filename
    try:
        if file_path.is_file():
            with file_path.open('r+', encoding='utf-8') as file:
                content = file.read()
                if function_name in content:
                    logging.info(f'{logging.INFO} Function {function_name} already documented')
                else:
                    file.write(f'{file_content}\n\n')
        else:
            with file_path.open('w', encoding='utf-8') as file:
                real_filename = filename.split('.')[0] + '.py'
                file.write(f'""" Cette interface du fichier `{real_filename} a été générée automatiquement par `autodoc`. Si modification, ajoutez auteur : date de modification"""\n')
                file.write("from typing import Any\n\n")
                file.write(file_content)
    except Exception as e:
        logging.error(f'{logging.ERROR}, {e}')


LOG_PATH = Path(__file__).resolve().parent / "autodoc.log"

def get_iter_exemples(var: Iterable) -> str:
    aRepr = reprlib.Repr()
    return aRepr.repr(var)
# Reécriture de la fonction type pour avoir simplement le type et non '<class str>' par ex



def typename(var: Any) -> str:
    return type(var).__name__

# #TODO: faire en sorte que ce soit récursif
# def get_iter_types(var: Iterable) -> str:
#     if isinstance(var, str): 
#         return 'str'
#     if not var: return logtype(var)
#     if isinstance(var, dict):
#         type_keys = list({logtype(typ_var) for typ_var in var.keys()})
#         type_values = list({logtype(typ_var) for typ_var in var.values()})
#         type_keys = 'Any' if len(type_keys) > 1 else type_keys[-1]
#         type_values = 'Any' if len(type_values) > 1 else type_values[-1]
#         return f"dict[{type_keys}, {type_values}]"
#     elif len(list(var)) < 2:
#         return f"{logtype(var)}[{logtype(list(var)[-1])}"
#     else:
#         return (
#             f"{logtype(var)}[Any]"
#             if logtype(list(var)[0]) != logtype(list(var)[1])
#             else f"{logtype(var)}[{logtype(list(var)[-1])}]"
#         )

modulename = lambda x: type(x).__module__

def create_annotation(arg_val) -> str:
    """ Fonction essayant de dynamiquement déterminer l'annotation
        d'une variable.
    """
    if arg_val is None:
        return 'None'
    print(modulename(arg_val))
    return typename(arg_val)

def clsname(argval) -> str:
    """ Connaissant le type d'une classe, transforme
        sa representation en une str.
    """
    return 'None' if  argval is None else type(argval).__name__
        

def get_signature(func_name: str, all_args: dict[str, Any], return_val: Any) -> str:
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
    docstring += f'\n\t:returns: {resultat[0]}: {reprlib.repr(resultat[1])}\n\t"""\n\t...\n'
    return docstring


def autodoc(func, write=True):
    @wraps(func)  # If we want to chain decorators
    def wrapper(*args, **kwargs):
        resultat = func(*args, **kwargs)
        args_names = func.__code__.co_varnames[:len(args)]
        return_name = "" if resultat is None else func.__code__.co_varnames[-1]
        func_name = func.__name__
        all_args = dict(zip(args_names, args))
        all_args |= kwargs
        def_filename = os.path.basename(func.__code__.co_filename) # with_csv_diff.py : filename où la fonction est définie
        signature = get_signature(func_name=func_name, all_args=all_args, return_val=resultat)
        docstring = get_docstring(all_args, resultat=(return_name, resultat))
        autostring = signature + docstring
        if write:
            check_and_update_file(filename=f'{def_filename}i', file_content=autostring, function_name=func_name)
        else:
            print(autostring)
        return resultat

    return wrapper