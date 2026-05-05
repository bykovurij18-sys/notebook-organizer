"""
JSON-хранилище заметок для Notebook Organizer.

Класс JSONStorage обеспечивает сохранение и загрузку заметок
из файла в формате JSON с поддержкой резервного копирования.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .models import Note, note_from_dict

if TYPE_CHECKING:
    pass


class StorageError(Exception):
    """Ошибка при работе с хранилищем."""


class JSONStorage:
    """Хранилище заметок на основе JSON-файла.

    Атрибуты:
        path (Path): Путь к файлу хранилища.
    """

    DEFAULT_FILENAME: str = "notes.json"
    BACKUP_SUFFIX: str = ".bak"
    ENCODING: str = "utf-8"
    INDENT: int = 2

    def __init__(self, path: str | Path | None = None) -> None:
        if path is None:
            path = Path.home() / ".notebook_organizer" / self.DEFAULT_FILENAME
        self._path: Path = Path(path)

    # ------------------------------------------------------------------
    # Публичные методы
    # ------------------------------------------------------------------

    @property
    def path(self) -> Path:
        """Путь к файлу хранилища."""
        return self._path

    def save(self, notes: list[Note]) -> None:
        """Сохраняет список заметок в JSON-файл.

        Перед записью создаёт резервную копию существующего файла.

        Args:
            notes: Список заметок для сохранения.

        Raises:
            StorageError: При ошибке записи файла.
        """
        self._ensure_directory()
        data: list[dict[str, Any]] = [note.to_dict() for note in notes]
        payload: dict[str, Any] = {
            "version": 1,
            "count": len(data),
            "notes": data,
        }
        # Создаём резервную копию перед перезаписью
        if self._path.exists():
            backup = self._path.with_suffix(self.BACKUP_SUFFIX)
            shutil.copy2(self._path, backup)
        try:
            tmp_path = self._path.with_suffix(".tmp")
            tmp_path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=self.INDENT),
                encoding=self.ENCODING,
            )
            tmp_path.replace(self._path)
        except OSError as exc:
            raise StorageError(f"Ошибка записи файла '{self._path}': {exc}") from exc

    def load(self) -> list[Note]:
        """Загружает заметки из JSON-файла.

        Returns:
            Список заметок. Если файл не существует, возвращает пустой список.

        Raises:
            StorageError: При ошибке чтения или разбора файла.
        """
        if not self._path.exists():
            return []
        try:
            raw = self._path.read_text(encoding=self.ENCODING)
            payload = json.loads(raw)
        except OSError as exc:
            raise StorageError(f"Ошибка чтения файла '{self._path}': {exc}") from exc
        except json.JSONDecodeError as exc:
            raise StorageError(
                f"Файл '{self._path}' содержит некорректный JSON: {exc}"
            ) from exc

        if not isinstance(payload, dict) or "notes" not in payload:
            raise StorageError(
                f"Файл '{self._path}' имеет неожиданную структуру (ожидается ключ 'notes')."
            )

        notes: list[Note] = []
        for i, item in enumerate(payload["notes"]):
            try:
                notes.append(note_from_dict(item))
            except (KeyError, ValueError, TypeError) as exc:
                raise StorageError(
                    f"Ошибка при разборе заметки #{i}: {exc}"
                ) from exc
        return notes

    def delete_file(self) -> None:
        """Удаляет файл хранилища (используется в тестах)."""
        if self._path.exists():
            self._path.unlink()
        backup = self._path.with_suffix(self.BACKUP_SUFFIX)
        if backup.exists():
            backup.unlink()

    def exists(self) -> bool:
        """Возвращает True, если файл хранилища существует."""
        return self._path.exists()

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    def _ensure_directory(self) -> None:
        """Создаёт директорию для файла хранилища, если она не существует."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def __repr__(self) -> str:
        return f"JSONStorage(path={self._path!r})"
