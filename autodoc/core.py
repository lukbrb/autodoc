from dataclasses import dataclass
import inspect
import os
import reprlib
from typing import Any, Callable, Iterable
from inspect import Signature, Parameter


class FuncDef:
    """ Classe qui créé une signature de fonction typée si elle n'existe pas."""
    def __init__(self, fonction: Callable) -> None:
        self.signature = inspect.signature(fonction) # type: ignore
        self.name = fonction.__name__

    def __repr__(self) -> str:
        return f"def {self.name}{str(self.signature)}:"
    
    def __str__(self) -> str:
        return f"def {self.name}{str(self.signature)}:"


@dataclass
class Argument:
    name: str
    annotation: Any
    value: Any


class Arguments:
    def __init__(self, args: tuple, kwargs: dict) -> None:
        self.args = args
        self.kwargs = kwargs
        self.all_values = list(args) + list(kwargs.values())
    


class DocString:
    """ Classe structurant la docstring de la fonction.
        Doit donner des exemples des arguments passés, 
        ainsi que permettre de choisir le format de documentation choisi.
    """

    def __init__(self, fonction: Callable, func_def: FuncDef, arguments: Arguments) -> None:
        self.fonction = fonction
        self.currentdoc = inspect.getdoc(fonction)
        self.signature = func_def.signature
        self.arguments = arguments.get_formatted_args()

    def get_args_examples(self) -> str:
        currentdoc = self.currentdoc or ""
        for argument in self.arguments:
            currentdoc += f'\n\t-{argument.name} : {argument.annotation} = {reprlib.repr(argument.value)}'
        return currentdoc
    
    def __str__(self) -> str:
        return self.get_args_examples()
    

class Fonction:
    """ Classe enrobant l'object fonction afin d'y ajouter des méthodes
        de convénience pour créer la doctstring.
    """

    def __init__(self, py_function: Callable, pos_arguments: tuple, key_arguments: dict) -> None:
        self.fonction = py_function
        self.arguments = Arguments(pos_arguments, key_arguments)
        self.func_def = FuncDef(self.fonction)
        self.docstring = DocString(self.fonction, self.func_def, self.arguments)

    @property
    def fromfile(self) -> str:
        return os.path.basename(self.fonction.__code__.co_filename)  # TODO: remplacer os par Pathlib
    
    def get_formatted_args(self):
        return self._structure_args()
    

    def _structure_args(self) -> list[Argument]:
        """ Structure les tuple args et dico kwargs
            en une liste de `Argument`.
        """
        return [
            Argument(arg.name, arg.annotation, argvalue)
            for arg, argvalue in zip(
                self.func_def.signature.parameters.values(), self.arguments.all_values
            )
        ]
    def _complete_args(self) -> list[Argument]:
        """ Vérifie si tous les arguments sont annotés,
            et essaie de les annoter si ils ne le sont pas.
            A ce stade, les annotations sont encore sous forme
            de classe. On extrait seulement le nom.
        """
        all_args = self._structure_args()
        for argument in all_args:
            print(argument)
            if argument.annotation is inspect._empty:
                argument.annotation = create_annotation(argument.value)
            else: 
                argument.annotation = type_to_str(argument.annotation)
        return all_args

    def _complete_signature(self) -> Signature:
        arguments = self.complete_args()
        # Note: on ne prend pas en compte le 'kind', peu important dans notre cas
        parameters = [Parameter(param.name, Parameter.VAR_POSITIONAL, annotation=param.annotation) for param in arguments]
        return Signature(parameters=parameters)
    

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
