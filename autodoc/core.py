from dataclasses import dataclass
import inspect
from pathlib import Path
import re
import reprlib
import types
from typing import Any, Callable, Union
from inspect import Signature


@dataclass
class Argument:
    name: str
    annotation: Any
    value: Any
    module: str

    def __str__(self) -> str:
        return f"{self.name}: {self.annotation}"

        
def evaluate_type(argument: Argument) -> Argument:
    """Complète l'annotation et le module d'un argument.

    On souhaite déterminer ici le module associé à une classe car 
    notre méthode renvoie l'annotation sous forme de `str`. 
    Le module auquel la classe appartient est sinon perdu.
    Note: On peut utiliser sinon la fonction `eval`
    Args:
        argument (Argument): Argument non complet.

    Returns:
        Argument: Copie de l'argument complété d'une annotation et d'un module associé.
    """
    if argument.value is None:
        annotation = "None"
    else:
        annotation = type(argument.value).__name__
    module = type(argument.value).__module__
    argument = Argument(argument.name, annotation, argument.value, module)
    return argument


def render_object(obj) -> str:
    """Renvoie un affichage lisible si la classe 
    n'implémente pas de méthode __str__ destinée aux humains.

    Args:
        obj (Any): L'objet qu'on veut afficher.

    Returns:
        str: Une représentation simplifiée de la classe.
    """

    # Par défaut, un objet sans __str__ affichera <maclasse object at 0x0000000>
    pattern = "object at"
    if pattern in str(obj):
        representation = str(obj).split(pattern)[0]
        representation = representation.replace("<", "")
        representation = representation.replace("", "")
    else:
        representation = reprlib.repr(obj)
    return representation

# Importé de la bibliothèque inspect
def formatannotation(annotation, base_module=None):
    if getattr(annotation, '__module__', None) == 'typing':
        def repl(match):
            text = match.group()
            return text.removeprefix('typing.')
        return re.sub(r'[\w\.]+', repl, repr(annotation))
    if isinstance(annotation, types.GenericAlias):
        return str(annotation)
    if isinstance(annotation, type):
        if annotation.__module__ in ('builtins', base_module):
            return annotation.__qualname__
        return f'{annotation.__module__}.{annotation.__qualname__}'
    return repr(annotation)

class Autodoc:
    """ Structure de l'auto-documentation.

    Attributes:
        function: La fonction que l'on souhaite documenter.
        funcname: Le nom de la fonction.
        arguments: Une liste d'objets `Argument`.
        signature: La signature de la fonction, évaluée par `inspect.signature`
        retval: Object `Argument`, contenant le nom de la variable de retour, son annotation, sa valeur et son module.
        filename: Chemin vers le fichier où la fonction est créée.
        style: Le style de documentation souhaité pour l'écriture de l'interface. Les options possibles sont :Google, Numpy et Sphinx.
        paramfile: Le chemin vers le fichier de paramètres.
    """
    quotestyle = '"""'
    def __init__(self, function: Callable, args: tuple[Any], kwargs: dict[str, Any], 
                 retval: Any, style: str = "Google", 
                 paramfile: Union[str, Path, None] = None) -> None:
        """Initialisation de la classe Autodoc

        Args:
            function (Callable): La fonction que l'on souhaite documenter.
            args (tuple[Any]): Un tuple contenant les arguments positionnels passés à la fonction.
            kwargs (dict[str, Any]): Un dictionnaire contenant les arguments passés avec le nom de l'argument.
            retval (Any): La valeur renvoyée par la fonction, son résultat.
            style (str, optional): Le style de documentation souhaité pour l'écriture de l'interface. Les options possibles sont :Google, Numpy et Sphinx. Par défaut à "Google".
            paramfile (str | Path | None, optional): Le chemin vers le fichier de paramètres. Par défaut à None.
        """
        self.function = function
        self.funcname = function.__name__
        self.signature = inspect.signature(function)
        self._all_values = list(args) + list(kwargs.values())
        self.arguments = self._get_args_types([Argument(arg.name, arg.annotation, argvalue, module="") for arg, argvalue in zip(self.signature.parameters.values(), self._all_values)])
        self._modules = {arg.module : set() for arg in self.arguments}  # Pour dynamiquement créer l'import de classes non définies dans les builtins
        self.retval = self._get_return_type(Argument(name="", annotation=self.signature.return_annotation, value=retval, module=""))
        self._docstring = inspect.getdoc(function)
        self.filename = function.__code__.co_filename
        self.style = style
        self.paramfile = paramfile
    
    def _get_args_types(self, arguments: list[Argument]) -> list[Argument]:
        """Complète l'annotation des arguments.

        Args:
            arguments (list[Argument]): Liste d'objets `Argument` à compléter.

        Returns:
            list[Argument]: Liste d'objets `Argument` complets.
        """
        for i, arg in enumerate(arguments):
            if arg.annotation is Signature.empty or arg.annotation is None or arg.value is None:
                arguments[i] = evaluate_type(arg)
            else: #  annotation déjà fournie par `signature`, nécessite de déterminer le module néanmoins
                arguments[i].annotation = type(arg.value).__name__
                arguments[i].module = type(arg.annotation).__module__
        return arguments
    
    def _get_return_type(self, retour: Argument) -> Argument:
        """Complète l'annotation de la valeur de retour.

        Args:
            arguments (list[Argument]): Valeur de retour `Argument` à compléter.

        Returns:
            list[Argument]: Valeur de retour `Argument` complète.
        """
        if retour.annotation is Signature.empty or retour.annotation is None or retour.value is None:
            retour = evaluate_type(retour)
        else:
            retour.annotation = type(retour.value).__name__
            retour.module = type(retour.annotation).__module__
        retour.name = "" if retour.value is None else self.function.__code__.co_varnames[-1]
        return retour
    

    def _fill_imports(self) -> None:
        """Met à jour le dictionnaire d'imports via la liste des `Argument`.
        
        """
        all_objects = self.arguments + [self.retval]  # Mieux de faire une copie en ajoutant le retour pour être exhaustif
        for argument in all_objects:
            if self._modules.get(argument.module):
                self._modules[argument.module].add(argument.annotation)
            else:
                self._modules[argument.module] = {argument.annotation}
    
    def _get_args_examples(self) -> str:
        code_examples = ""
        for argument in self.arguments:
            code_examples += f"\t\t>>> {argument.name}\n"
            code_examples += f"\t\t{render_object(argument.value)}\n"

        return code_examples

    def build_docstring(self) -> str:
        new_doc = f"\t{Autodoc.quotestyle} Fonction {self.funcname}\n"  # TODO: prendre en compte une éventuelle docstring existante (self._docstring if self._docstring else) 
        new_doc += "\tArgs:\n"
        for argument in self.arguments:
            new_doc += f"\t\t{argument.name} ({argument.annotation})\n"
        if self.retval.value:
            new_doc += "\n\tReturns:\n"
            new_doc += f'\t\t{self.retval.name} ({self.retval.annotation})\n'
        new_doc += "\n\tExamples:\n"
        new_doc += self._get_args_examples()
        new_doc += f"\t\t>>> {self.funcname}(...)\n"
        new_doc += f"\t\t{render_object(self.retval.value)}"
        return str(self._docstring) + new_doc

    def generate_imports(self) -> str:
        """Ajoute les imports des classes nécessaires.

        Returns:
            str: Une chaîne de caractère comprenant les imports.
        """
        module_imports = ""
        cls_defs = ""
        self._fill_imports()
        for module, classes in self._modules.items():
            if module == '__main__':  # C'est une classe définie dans le fichier
                for clsname in self._modules[module]:
                    cls_defs += self._generate_class_def(clsname)
            if  module != "builtins":
                module_imports += f"from {module} import {','.join(classes)}\n"
        return module_imports + cls_defs


    def _generate_class_def(self, clsname: str) -> str:
        """ Génère la création d'une classe vide.

            Note: 
                La prise en charge des classes sera faite en v2.

            Args:
                clsname (str): Le nom de la classe 
            Returns:
                Une chaîne de caractère déinissant une classe
        """
        clsdef = "\n\n"
        clsdef += f"class {clsname}:\n"
        clsdef += "\t...\n\n"
        return clsdef


    def _render_signature(self) -> str:
        arguments = [str(argument) for argument in self.arguments]
        return f"def {self.funcname}({', '.join(arguments)}) -> {self.retval.annotation}:\n"
    
    def generate_full_doc(self) -> str:
        fulldoc = self._render_signature()
        fulldoc += self.build_docstring()
        fulldoc += f"\n\t{Autodoc.quotestyle}\n"
        fulldoc += "\t...\n"
        return fulldoc
    