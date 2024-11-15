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
realtype = type
def type(var: Any) -> str:
    if var is None:
        return 'None'
    elif isinstance(var, Iterable):
        return get_iter_types(var)
    else:
        return realtype(var).__name__
     

def logtype(var: Any) -> str:
    return realtype(var).__name__

#TODO: faire en sorte que ce soit récursif
def get_iter_types(var: Iterable) -> str:
    if isinstance(var, str): 
        return 'str'
    if not var: return logtype(var)
    if isinstance(var, dict):
        if var:
            type_keys = list({logtype(typ_var) for typ_var in var.keys()})
            type_values = list({logtype(typ_var) for typ_var in var.values()})
            type_keys = 'Any' if len(type_keys) > 1 else type_keys[-1]
            type_values = 'Any' if len(type_values) > 1 else type_values[-1]
            return f"dict[{type_keys}, {type_values}]"
        else:
            return "dict"
    elif len(list(var)) < 2:
        return f"{logtype(var)}[{logtype(list(var)[-1])}"
    else:
        return (
            f"{logtype(var)}[Any]"
            if logtype(list(var)[0]) != logtype(list(var)[1])
            else f"{logtype(var)}[{logtype(list(var)[-1])}]"
        )

class FuncDef:
    """ Classe qui créé une signature de fonction typée si elle n'existe pas."""
    def __init__(self, fonction: Callable) -> None:
        self.signature = inspect.signature(fonction) # type: ignore
        self.name = fonction.__name__
    
    def __repr__(self) -> str:
        return f"def {self.name}{str(self.signature)}:"
    
    def __str__(self) -> str:
        return f"def {self.name}{str(self.signature)}:"
    

class Arguments:
    def __init__(self, args: tuple, kwargs: dict) -> None:
        self.args = args
        self.kwargs = kwargs


class DocString:
    """ Classe structurant la docstring de la fonction.
        Doit donner des exemples des arguments passés, 
        ainsi que permettre de choisir le format de documentation choisi.
    """

    def __init__(self, fonction: Callable, func_def: FuncDef) -> None:
        self.fonction = fonction
        self.currentdoc = inspect.getdoc(fonction)
        self.signature = func_def.signature


    def get_args_examples(self) -> str:
        currentdoc = self.currentdoc if self.currentdoc else ""
        print(self.signature.parameters)
        for name, value in self.signature.parameters.items():
            currentdoc += f'\n\t-{name} : {reprlib.repr(value)}' # type: ignore
        return currentdoc
    
    def __str__(self) -> str:
        return self.get_args_examples()


class Fonction:
    """ Classe enrobant l'object fonction afin d'y ajouter des méthodes
        de convénience pour créer la doctstring.
    """

    def __init__(self, fonction: Callable) -> None:
        self.fonction = fonction
    
    @property
    def signature(self) -> FuncDef:
        return FuncDef(self.fonction)
    
    @property
    def docstring(self) -> DocString:
        return DocString(self.fonction, self.signature)

    @property
    def fromfile(self) -> str:
        return os.path.basename(self.fonction.__code__.co_filename)  # TODO: remplacer os par Pathlib
    
class Documentation:
    """ Classe s'occupant de la mise en place de toutes les pièces
        nécessaires à la documentation du code.
    """
    def __init__(self, func_def: FuncDef, docstring: DocString, delimiter:str = '"""', style = None) -> None:
        self.func_def = func_def
        self.docstring = docstring
        self.delimiter = delimiter
        self.style = style
        self.docu = ""
    
    @property
    def representation(self) -> str:
        self.docu += str(self.func_def)
        self.docu += f"\n\t{self.delimiter}\n\t"
        self.docu += str(self.docstring)
        self.docu += f"\n\t{self.delimiter}\n\t"
        self.docu += "\n\t..."
        return self.docu


def autodoc(func):

    @wraps(func)  # If we want to chain decorators
    def wrapper(*args, **kwargs):
        resultat = func(*args, **kwargs)
        fd = FuncDef(func)
        ds = DocString(func, fd)
        docu = Documentation(fd, ds)
        autostring = docu.representation
    
        # args_names = func.__code__.co_varnames[:len(args)]
        # return_name = func.__code__.co_varnames[-1]
        def_filename = os.path.basename(func.__code__.co_filename) # with_csv_diff.py : filename où la fonction est définie
        # autostring = f"\ndef {func.__name__}"
        # arguments = ""
        # karguments = ""
        # docstring = "\t'''\n\t:params:\n"
        # for arg_name, arg_val in zip(args_names, args): 
        #     arguments += f"{(arg_name)}: {type(arg_val)}, "
        #     docstring += f"\t-{(arg_name)}: {get_iter_exemples(arg_val)}\n"
        # for k, v in kwargs.items():
        #     karguments += f"{k}: {type(v)} = {v}, "
        #     docstring += f"\t-{k}: = {get_iter_exemples(v)}\n"
        # arguments += karguments
        # arguments = arguments.rstrip(", ") # supprime la dernière virgule avant de refermer parenthèse
        # autostring += f"({arguments}) -> {type(resultat)}:\n"
        # autostring += docstring
        # autostring += f"\n\t:returns: {return_name}: {get_iter_exemples(resultat)}\n\t'''\n\t..."
        check_and_update_file(filename=f'{def_filename}i', file_content=autostring, function_name=func.__name__)
        return resultat

    return wrapper