"""
Фильтрация заметок для Notebook Organizer.

Класс NoteFilter предоставляет статические методы для фильтрации
коллекций заметок по различным критериям.
"""

from __future__ import annotations

from datetime import datetime, date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import Note


class NoteFilter:
    """Статический класс для фильтрации коллекций заметок."""

    # ------------------------------------------------------------------
    # Фильтрация по тегам
    # ------------------------------------------------------------------

    @staticmethod
    def by_tag(notes: list["Note"], tag: str) -> list["Note"]:
        """Возвращает заметки, содержащие указанный тег.

        Args:
            notes: Исходный список заметок.
            tag:   Тег для поиска (регистр не учитывается).

        Returns:
            Список заметок, содержащих данный тег.
        """
        tag = tag.strip().lower()
        return [n for n in notes if n.has_tag(tag)]

    @staticmethod
    def by_tags_all(notes: list["Note"], tags: list[str]) -> list["Note"]:
        """Возвращает заметки, содержащие ВСЕ указанные теги.

        Args:
            notes: Исходный список заметок.
            tags:  Список тегов (все должны присутствовать).
        """
        normalized = [t.strip().lower() for t in tags]
        return [n for n in notes if all(n.has_tag(t) for t in normalized)]

    @staticmethod
    def by_tags_any(notes: list["Note"], tags: list[str]) -> list["Note"]:
        """Возвращает заметки, содержащие ХОТЯ БЫ ОДИН из указанных тегов.

        Args:
            notes: Исходный список заметок.
            tags:  Список тегов (хотя бы один должен присутствовать).
        """
        normalized = [t.strip().lower() for t in tags]
        return [n for n in notes if any(n.has_tag(t) for t in normalized)]

    # ------------------------------------------------------------------
    # Фильтрация по дате
    # ------------------------------------------------------------------

    @staticmethod
    def by_date(notes: list["Note"], target_date: date) -> list["Note"]:
        """Возвращает заметки, созданные в указанный календарный день.

        Args:
            notes:       Исходный список заметок.
            target_date: Дата для фильтрации (объект date или datetime).
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        return [n for n in notes if n.date.date() == target_date]

    @staticmethod
    def by_date_range(
        notes: list["Note"],
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list["Note"]:
        """Возвращает заметки в заданном диапазоне дат (включительно).

        Args:
            notes: Исходный список заметок.
            start: Начало диапазона (None — без ограничения снизу).
            end:   Конец диапазона (None — без ограничения сверху).
        """
        result = notes
        if start is not None:
            result = [n for n in result if n.date >= start]
        if end is not None:
            result = [n for n in result if n.date <= end]
        return result

    @staticmethod
    def by_date_after(notes: list["Note"], after: datetime) -> list["Note"]:
        """Возвращает заметки, созданные после указанной даты."""
        return [n for n in notes if n.date > after]

    @staticmethod
    def by_date_before(notes: list["Note"], before: datetime) -> list["Note"]:
        """Возвращает заметки, созданные до указанной даты."""
        return [n for n in notes if n.date < before]

    # ------------------------------------------------------------------
    # Фильтрация по типу
    # ------------------------------------------------------------------

    @staticmethod
    def by_type(notes: list["Note"], note_type: str) -> list["Note"]:
        """Возвращает заметки указанного типа.

        Args:
            notes:     Исходный список заметок.
            note_type: Тип заметки: 'text', 'voice' или 'checklist'.
        """
        note_type = note_type.strip().lower()
        return [n for n in notes if n.note_type == note_type]

    # ------------------------------------------------------------------
    # Полнотекстовый поиск
    # ------------------------------------------------------------------

    @staticmethod
    def by_title(notes: list["Note"], query: str) -> list["Note"]:
        """Возвращает заметки, заголовок которых содержит строку запроса.

        Args:
            notes: Исходный список заметок.
            query: Строка поиска (регистр не учитывается).
        """
        query = query.strip().lower()
        return [n for n in notes if query in n.title.lower()]

    # ------------------------------------------------------------------
    # Сортировка
    # ------------------------------------------------------------------

    @staticmethod
    def sort_by_date(notes: list["Note"], descending: bool = True) -> list["Note"]:
        """Сортирует заметки по дате.

        Args:
            notes:      Исходный список заметок.
            descending: True — новые сначала; False — старые сначала.
        """
        return sorted(notes, key=lambda n: n.date, reverse=descending)

    @staticmethod
    def sort_by_title(notes: list["Note"], descending: bool = False) -> list["Note"]:
        """Сортирует заметки по заголовку в алфавитном порядке."""
        return sorted(notes, key=lambda n: n.title.lower(), reverse=descending)
