from dataclasses import dataclass
import inspect
import logging
import os
from pathlib import Path
import reprlib
from typing import Any, Callable, Iterable
from inspect import Signature, Parameter

@dataclass
class Argument:
    name: str
    annotation: Any
    value: Any
    module: str

    def __str__(self) -> str:
        return f"{self.name}: {self.annotation}"

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
                # file.write(f'""" Cette interface du fichier `{real_filename} a été générée automatiquement par `autodoc`. Si modification, ajoutez auteur : date de modification"""\n')
                # file.write("from typing import Any\n\n")
                file.write(file_content)
    except Exception as e:
        logging.error(f'{logging.ERROR}, {e}')

        
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
    if argument is None:
        annotation = "None"
    else:
        annotation = type(argument.value).__name__
    module = type(argument.value).__module__
    return Argument(argument.name, annotation, argument.value, module) 


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
                 paramfile: str | Path | None = None) -> None:
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
        self._modules = {arg.module : [] for arg in self.arguments}  # Pour dynamiquement créer l'import de classes non définies dans les builtins
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
        for arg in arguments:
            if not arg.annotation:
                arg = evaluate_type(arg.annotation)
            else: #  annotation déjà fournie par `signature`, nécessite de déterminer le module néanmoins
                arg.module = type(arg.annotation).__module__        
        return arguments
    
    def _get_return_type(self, retour: Argument) -> Argument:
        """Complète l'annotation de la valeur de retour.

        Args:
            arguments (list[Argument]): Valeur de retour `Argument` à compléter.

        Returns:
            list[Argument]: Valeur de retour `Argument` complète.
        """
        if not retour.annotation:
            retour = evaluate_type(retour.annotation)
        retour.name = "" if retour.value is None else self.function.__code__.co_varnames[-1]
        return retour
    

    def _fill_imports(self) -> None:
        """Met à jour le dictionnaire d'imports via la liste des `Argument`.
        
        """
        for argument in self.arguments:
            if self._modules.get(argument.module):
                self._modules[argument.module].append(argument.annotation)
            else:
                self._modules[argument.module] = [argument.annotation]
    
    def _get_args_examples(self) -> str:
        code_examples = ""
        for argument in self.arguments:
            # currentdoc += f'\n\t\t{argument.name} ({argument.annotation}) = {reprlib.repr(argument.value)}'
            code_examples += f"\t\t>>> {argument.name}\n"
            code_examples += f"\t\t{render_object(argument.value)}\n"

        return code_examples

    def build_docstring(self) -> str:
        new_doc = self._docstring if self._docstring else f"\t{Autodoc.quotestyle}\n"
        new_doc = "\tArgs:\n"
        for argument in self.arguments:
            new_doc += f"\t\t{argument.name} ({argument.annotation})\n"
        if self.retval.value:
            new_doc += "\tReturns:"
            new_doc += f'\t\t{self.retval.name} ({self.retval.annotation})\n'
        new_doc += self._get_args_examples()
        new_doc += f"\t\t>>> {self.retval.name}\n"
        new_doc += f"\t\t{render_object(self.retval.value)}"
        return new_doc

    def generate_imports(self) -> str:
        """Ajoute les imports des classes nécessaires.

        Returns:
            str: Une chaîne de caractère comprenant les imports.
        """
        module_imports = ""
        self._fill_imports()
        for module, classes in self._modules.items():
            if not module == "builtins":
                module_imports += f"from {module} import {','.join(classes)}\n"
        return module_imports

    def _render_signature(self) -> str:
        arguments = [str(argument) for argument in self.arguments]
        return f"def {self.funcname}({', '.join(arguments)}) -> {self.retval.annotation}:\n"
    
    def generate_full_doc(self) -> str:
        fulldoc = self._render_signature()
        fulldoc += self.build_docstring()
        fulldoc += f"\n\t{Autodoc.quotestyle}\n"
        fulldoc += "\t..."
        return fulldoc
    