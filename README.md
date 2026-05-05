#!/usr/bin/env python3
"""
Notebook Organizer — точка входа в приложение.

Запуск:
    python main.py
    python main.py --storage /path/to/notes.json
"""

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="notebook-organizer",
        description="Консольный органайзер заметок с поддержкой CRUD, "
                    "фильтрации, отмены действий и JSON-хранилища.",
    )
    parser.add_argument(
        "--storage",
        metavar="PATH",
        default=None,
        help="Путь к JSON-файлу хранилища (по умолчанию: ~/.notebook_organizer/notes.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Импортируем здесь, чтобы ошибки импорта были понятны пользователю
    try:
        from notebook.manager import NoteManager
        from notebook.storage import JSONStorage
        from notebook.cli import NotebookCLI
    except ImportError as exc:
        print(f"Ошибка импорта: {exc}", file=sys.stderr)
        print("Убедитесь, что вы запускаете приложение из корневой директории проекта.", file=sys.stderr)
        sys.exit(1)

    storage = JSONStorage(args.storage) if args.storage else JSONStorage()
    manager = NoteManager(storage=storage)
    app = NotebookCLI(manager=manager)

    try:
        app.run()
    except Exception as exc:  # noqa: BLE001
        print(f"\nНепредвиденная ошибка: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
