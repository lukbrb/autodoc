from pathlib import Path
import logging

def check_and_update_file(filepath: str, file_content: str, function_name: str) -> None:
    logging.basicConfig(filename='messages.log', level=logging.DEBUG)

    typing_dir = Path('typings')
    file_name = Path(filepath).name
    print(file_name)
    typing_dir.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Dossier cree à {typing_dir=}")

    # Combiner le chemin du dossier avec le nom du fichier
    file_path = typing_dir / file_name
    
    # Écrire dans le fichier
    logging.info(f"Ecriture du fichier à l'emplacement{file_path=}")
    try:
        if file_path.is_file():
            with file_path.open('r+', encoding='utf-8') as file:
                content = file.read()
                if function_name in content:
                    logging.info(f'{logging.INFO} Function {function_name} already documented')
                else:
                    file.write(f'{file_content}\n\n')
        else:
            file_path.write_text(file_content)
    except Exception as e:
        logging.error(f'{logging.ERROR}, {e}')
