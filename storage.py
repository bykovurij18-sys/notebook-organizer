"""
Валидаторы входных данных для Notebook Organizer.

Все методы класса NoteValidator являются статическими и выбрасывают
ValueError или TypeError при обнаружении некорректных данных.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

from .models import DATE_FORMAT, NOTE_TYPES


class NoteValidator:
    """Статический класс для проверки корректности данных заметок."""

    TAG_PATTERN: re.Pattern = re.compile(r"^[a-zA-Zа-яёА-ЯЁ0-9_\-]+$")

    # ------------------------------------------------------------------
    # Заголовок
    # ------------------------------------------------------------------

    @staticmethod
    def validate_title(title: Any) -> str:
        """Проверяет и нормализует заголовок заметки."""
        if not isinstance(title, str):
            raise TypeError(f"Заголовок должен быть строкой, получено: {type(title).__name__}.")
        title = title.strip()
        if not title:
            raise ValueError("Заголовок не может быть пустым или состоять только из пробелов.")
        if len(title) > 200:
            raise ValueError(f"Заголовок слишком длинный ({len(title)} символов, максимум 200).")
        return title

    # ------------------------------------------------------------------
    # Теги
    # ------------------------------------------------------------------

    @staticmethod
    def validate_tags(tags: Any) -> list[str]:
        """Проверяет список тегов и возвращает нормализованный список."""
        if not isinstance(tags, list):
            raise TypeError(f"Теги должны быть списком, получено: {type(tags).__name__}.")
        if len(tags) > 20:
            raise ValueError(f"Слишком много тегов ({len(tags)}, максимум 20).")
        result: list[str] = []
        seen: set[str] = set()
        for tag in tags:
            if not isinstance(tag, str):
                raise TypeError(f"Каждый тег должен быть строкой, получено: {type(tag).__name__}.")
            tag = tag.strip().lower()
            if not tag:
                raise ValueError("Тег не может быть пустой строкой.")
            if not NoteValidator.TAG_PATTERN.match(tag):
                raise ValueError(
                    f"Тег '{tag}' содержит недопустимые символы. "
                    "Разрешены: буквы, цифры, дефис и подчёркивание."
                )
            if tag in seen:
                continue  # дубликаты молча пропускаем
            seen.add(tag)
            result.append(tag)
        return result

    # ------------------------------------------------------------------
    # Дата
    # ------------------------------------------------------------------

    @staticmethod
    def validate_date_string(date_str: Any) -> datetime:
        """Парсит строку даты в формате DATE_FORMAT."""
        if not isinstance(date_str, str):
            raise TypeError(f"Дата должна быть строкой, получено: {type(date_str).__name__}.")
        try:
            return datetime.strptime(date_str, DATE_FORMAT)
        except ValueError:
            raise ValueError(
                f"Неверный формат даты: '{date_str}'. Ожидается: YYYY-MM-DD HH:MM:SS."
            )

    # ------------------------------------------------------------------
    # Тип заметки
    # ------------------------------------------------------------------

    @staticmethod
    def validate_note_type(note_type: Any) -> str:
        """Проверяет корректность типа заметки."""
        if not isinstance(note_type, str):
            raise TypeError(f"Тип заметки должен быть строкой, получено: {type(note_type).__name__}.")
        note_type = note_type.strip().lower()
        if note_type not in NOTE_TYPES:
            raise ValueError(
                f"Неизвестный тип заметки: '{note_type}'. "
                f"Допустимые значения: {', '.join(NOTE_TYPES)}."
            )
        return note_type

    # ------------------------------------------------------------------
    # Текст
    # ------------------------------------------------------------------

    @staticmethod
    def validate_text(text: Any, max_length: int = 10_000, field_name: str = "Текст") -> str:
        """Проверяет текстовое поле заметки."""
        if not isinstance(text, str):
            raise TypeError(f"{field_name} должен быть строкой, получено: {type(text).__name__}.")
        if len(text) > max_length:
            raise ValueError(
                f"{field_name} слишком длинный ({len(text)} символов, максимум {max_length})."
            )
        return text

    # ------------------------------------------------------------------
    # Числовые поля
    # ------------------------------------------------------------------

    @staticmethod
    def validate_duration(duration: Any) -> int:
        """Проверяет длительность голосовой заметки в секундах."""
        if not isinstance(duration, int):
            try:
                duration = int(duration)
            except (TypeError, ValueError):
                raise TypeError("Длительность должна быть целым числом.")
        if duration < 0:
            raise ValueError("Длительность не может быть отрицательной.")
        if duration > 10_800:
            raise ValueError("Длительность не может превышать 10 800 секунд (3 часа).")
        return duration

    # ------------------------------------------------------------------
    # Пункты чеклиста
    # ------------------------------------------------------------------

    @staticmethod
    def validate_checklist_items(items: Any) -> list[dict]:
        """Проверяет список пунктов чеклиста."""
        if not isinstance(items, list):
            raise TypeError(f"Пункты чеклиста должны быть списком, получено: {type(items).__name__}.")
        if len(items) > 100:
            raise ValueError(f"Чеклист содержит слишком много пунктов ({len(items)}, максимум 100).")
        result: list[dict] = []
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                raise TypeError(f"Пункт #{i} должен быть словарём.")
            text = item.get("text", "")
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f"Текст пункта #{i} не может быть пустым.")
            if len(text) > 500:
                raise ValueError(f"Текст пункта #{i} слишком длинный (максимум 500 символов).")
            result.append({"text": text.strip(), "done": bool(item.get("done", False))})
        return result
