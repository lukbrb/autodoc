# Autodoc

Auto-documentation dynamique du code. Créé un fichier d'interface `.pyi` spécifiant le typage des fonctions décorée.
_____

## Plan d'action

L'idée de l'outil est de compléter le typage des fonctions, de créer une docstring des fonctions (via un LLM), puis de générer une documentation
via un  outil comme sphinx, par exemple.

## Utilisation

### 1. Typage

Pour créer un typage complet, `autodoc` évalue le type des arguments lors de l'éxécution (*runtime*) de la fonction. De ce fait,
`autodoc` s'utilise via un décorateur qui va créer un fichier d'interface `.pyi` (aussi appelé *stub file*).

Exemple d'utilisation :

``` python
# fichier_demo.py
from autodoc import autodoc

@autodoc
def ma_fonction(arg1, arg2, unautrearg=1):
    # Fait ses calculs ...
    unobjet = [arg1, arg2, unautrearg]
    return unobjet
```

Lorsque la fonction `ma_fonction` décorée de  `@autodoc` sera appelée, un fichier `.pyi` sera créé dans un dossier `typings` adjacent :

``` python
# fichier_demo.pyi

def ma_fonction(arg1: str, arg2: str, unautrearg: int=1) -> List[str, str, int]:
    """
        Fonction `ma_fonction`

        Args:
            arg1 (str)
            arg2 (str)
            unautrearg (int)
        Returns:
            unobjet (List[str, str, int])
    
        Exemples:

        >>> ma_fonction('a', 'b', 0)
        ['a', 'b', 0]
    """
    ...
```

> [!WARNING]  
> Il n'y a pour l'instant pas de manière de combiner les typages et docstring existants. Les typages seront remplacés, et les docstring concaténées.  

> [!TIP]  
> A terme, il sera possible de décider du type de documentation souhaité (Google, Sphinx, Numpy...) et de choisir d'afficher les exemples ou non.  

> [!NOTE]  
> Changement du 31/12/2024. Le fait d'écrire le typage et les exemples dans d'autres fichiers pose problème pour ensuite créer la documentation via le LLM, qui du coup n'a pas à la fois le contexte du typage ET du code en même temps. Une option prise à cette date est de copier l'entièreté du fichier `.py` à la place du fichier `.pyi`. Néanmois le choix de pouvoir seulement typer les fonctions dans un fichier interface devrait être gardé. Une solution doit être trouvée.

Une fois le décorateur mis en place, `autodoc` se charge de tout faire automatiquement. Mais que faire pour une base de code composée de centaines ou de milliers de fonctions ?  
`autodoc` fournit un outil en ligne de commande permettant de décorer toutes les fonctions de la base de code :

``` bash
autodoc-populate --dir <path/to/my/codebase>
```

>[!TIP]  
> Il est possible de spécifier dans un fichier de configuration les dossiers et fonctions à ignorer.
> Pas implémenté à ce jour (31/12/2024)

Une fois la documentation créé, les décorateurs peuvent automatiquement être enlevés avec la commande

``` bash
autodoc-depopulate --dir <path/to/my/codebase>
```

> [!WARNING]  
> Le formattage du code sera possiblement différent de l'original. POur l'ensemble de la procédure d'autodocumentation, il est recommandé de copier son répertoire de travail et de faire les manipulations de documentation sur cette copie.

### 2. Génération de docstring

A l'heure actuelle `autodoc` n'implémente pas de génération automatique de docstring. Le moyen le plus simple reste probablement l'utilisation de GitHub copilot en mode éditeur (pour qu'il puisse intéragir directement avec le code).

### 3. Génération de la documentation

La génération de documentation en fichiers `HTML`, `Markdown`, ou `PDF` n'est pas encore automatisée via l'API de `autodoc`, mais des outils comme `sphinx` font cela très bien.
L'automatisation de cette fonctionnalité est prévue dans une version future.

## Objets utilisés

Pour fonctionner, le module a besoin :

1. De la fonction à documenter. Via laquelle on peut avoir accès à la signature, le nom de la fonction, à la docstring, et au cadre (frame)
2. Le cadre permet de déterminer grand nombre de variables : le nom du fichier, le nom des arguments passés et de la variable retournée.
3. Des arguments. On utilise directement les valeurs des arguments passés à la fonction.
    - Dans le cas des arguments positionnels, on ne connait que leurs valeurs, mais pas leurs noms. Les arguments positionnels sont nécessairement passés dans le même ordre que dans la définition de la fonction. Ainsi, on peut utiliser la fonction `inspect.signature` pour déterminer les noms, ou bien la liste co_argnames qui est un attibut du cadre (`frame`). Il semble plus robuste d'utiliser la signature.
4. De la valeur du résultat retourné par la fonction. Ceci pour permettre de typer ce retour.
5. Du style de documentation souhaité. **Sera implémenté dans une v2**
6. D'un fichier de paramètres, pour par exemple spécifier le chemin vers lequel écrire les résultats. **Sera implémenté dans unen v2**

## Objets crées

Autodoc souhaite aussi donner des exemples des valeurs utilisées, ceci à l'aide de `reprlib.repr`, qui donne une représentation alternative, souvent simplifiée par des ellispes, des objets Python. Ceci pourrait être rendu optionnel.

Autodoc souhaite également pouvoir typer les structures de données contenaires récursivement. C'est-à-dire, pour un tuple de liste contenant des chaînes de caractère et des entiers par exemple, pouvoir typer : `tuple[list[str], list[int]]` plutôt que seulement `tuple`. A terme, on souhaiterait pouvoir spécifier la profondeur à laquelle effectuer le typage. **Sera implémenté dans une v2**

Finalement, grâce à la fonction `type` on peut savoir à quel module appartient une certaine classe. Si une classe n'est pas dans les `builtins`, on souhaiterait ajouter un import dans le fichier de sortie `.pyi`.

![Flux de création de l'auto-documentation.](ressources/image.png)
