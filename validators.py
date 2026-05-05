"""
Модели заметок для Notebook Organizer.

Иерархия классов:
    Note (абстрактный базовый класс)
    ├── TextNote   — обычная текстовая заметка
    ├── VoiceNote  — заметка с транскрипцией голосового сообщения
    └── ChecklistNote — заметка-чеклист с пунктами
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Вспомогательные константы
# ---------------------------------------------------------------------------

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
NOTE_TYPES = ("text", "voice", "checklist")


# ---------------------------------------------------------------------------
# Базовый класс
# ---------------------------------------------------------------------------

class Note(ABC):
    """Абстрактный базовый класс для всех типов заметок.

    Атрибуты:
        note_id (str): Уникальный идентификатор заметки (UUID4).
        title   (str): Заголовок заметки (не пустой, ≤ 200 символов).
        tags    (list[str]): Список тегов (каждый тег — строка без пробелов).
        date    (datetime): Дата и время создания/последнего изменения.
    """

    MAX_TITLE_LENGTH: int = 200
    MAX_TAGS: int = 20

    def __init__(
        self,
        title: str,
        tags: list[str] | None = None,
        date: datetime | None = None,
        note_id: str | None = None,
    ) -> None:
        self._note_id: str = note_id or str(uuid.uuid4())
        self.title: str = title
        self.tags: list[str] = tags or []
        self.date: datetime = date or datetime.now()

    # ------------------------------------------------------------------
    # Свойства
    # ------------------------------------------------------------------

    @property
    def note_id(self) -> str:
        """Идентификатор заметки (только для чтения)."""
        return self._note_id

    @property
    def title(self) -> str:
        return self._title

    @title.setter
    def title(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Заголовок должен быть строкой.")
        value = value.strip()
        if not value:
            raise ValueError("Заголовок не может быть пустым.")
        if len(value) > self.MAX_TITLE_LENGTH:
            raise ValueError(
                f"Заголовок не может превышать {self.MAX_TITLE_LENGTH} символов."
            )
        self._title = value

    @property
    def tags(self) -> list[str]:
        return list(self._tags)

    @tags.setter
    def tags(self, value: list[str]) -> None:
        if not isinstance(value, list):
            raise TypeError("Теги должны быть переданы в виде списка.")
        if len(value) > self.MAX_TAGS:
            raise ValueError(f"Нельзя добавить более {self.MAX_TAGS} тегов.")
        cleaned: list[str] = []
        for tag in value:
            if not isinstance(tag, str):
                raise TypeError(f"Тег должен быть строкой, получено: {type(tag)}.")
            tag = tag.strip().lower()
            if not tag:
                raise ValueError("Тег не может быть пустой строкой.")
            if " " in tag:
                raise ValueError(f"Тег не может содержать пробелы: '{tag}'.")
            cleaned.append(tag)
        self._tags: list[str] = cleaned

    @property
    def date(self) -> datetime:
        return self._date

    @date.setter
    def date(self, value: datetime) -> None:
        if not isinstance(value, datetime):
            raise TypeError("Дата должна быть объектом datetime.")
        self._date = value

    # ------------------------------------------------------------------
    # Абстрактные методы
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def note_type(self) -> str:
        """Тип заметки (строковый идентификатор)."""

    @abstractmethod
    def preview(self) -> str:
        """Краткое превью содержимого заметки (≤ 80 символов)."""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Сериализация заметки в словарь для JSON."""

    # ------------------------------------------------------------------
    # Общие методы
    # ------------------------------------------------------------------

    def _base_dict(self) -> dict[str, Any]:
        """Возвращает словарь с базовыми полями заметки."""
        return {
            "note_id": self._note_id,
            "note_type": self.note_type,
            "title": self._title,
            "tags": self._tags,
            "date": self._date.strftime(DATE_FORMAT),
        }

    def update_date(self) -> None:
        """Обновляет дату заметки до текущего момента."""
        self._date = datetime.now()

    def has_tag(self, tag: str) -> bool:
        """Проверяет наличие тега в заметке."""
        return tag.strip().lower() in self._tags

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"id={self._note_id[:8]}…, "
            f"title={self._title!r}, "
            f"tags={self._tags})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Note):
            return NotImplemented
        return self._note_id == other._note_id

    def __hash__(self) -> int:
        return hash(self._note_id)


# ---------------------------------------------------------------------------
# TextNote
# ---------------------------------------------------------------------------

class TextNote(Note):
    """Обычная текстовая заметка.

    Дополнительные атрибуты:
        text (str): Основной текст заметки (≤ 10 000 символов).
    """

    MAX_TEXT_LENGTH: int = 10_000

    def __init__(
        self,
        title: str,
        text: str = "",
        tags: list[str] | None = None,
        date: datetime | None = None,
        note_id: str | None = None,
    ) -> None:
        super().__init__(title=title, tags=tags, date=date, note_id=note_id)
        self.text: str = text

    @property
    def note_type(self) -> str:
        return "text"

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Текст заметки должен быть строкой.")
        if len(value) > self.MAX_TEXT_LENGTH:
            raise ValueError(
                f"Текст заметки не может превышать {self.MAX_TEXT_LENGTH} символов."
            )
        self._text = value

    def preview(self) -> str:
        snippet = self._text[:77]
        return snippet + "…" if len(self._text) > 77 else snippet

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["text"] = self._text
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TextNote":
        """Десериализация из словаря."""
        return cls(
            title=data["title"],
            text=data.get("text", ""),
            tags=data.get("tags", []),
            date=datetime.strptime(data["date"], DATE_FORMAT),
            note_id=data.get("note_id"),
        )


# ---------------------------------------------------------------------------
# VoiceNote
# ---------------------------------------------------------------------------

class VoiceNote(Note):
    """Заметка, представляющая транскрипцию голосового сообщения.

    Дополнительные атрибуты:
        transcription (str): Текст транскрипции.
        duration_sec  (int): Длительность голосового сообщения в секундах (≥ 0).
    """

    MAX_TRANSCRIPTION_LENGTH: int = 10_000
    MAX_DURATION_SEC: int = 3 * 3600  # 3 часа

    def __init__(
        self,
        title: str,
        transcription: str = "",
        duration_sec: int = 0,
        tags: list[str] | None = None,
        date: datetime | None = None,
        note_id: str | None = None,
    ) -> None:
        super().__init__(title=title, tags=tags, date=date, note_id=note_id)
        self.transcription: str = transcription
        self.duration_sec: int = duration_sec

    @property
    def note_type(self) -> str:
        return "voice"

    @property
    def transcription(self) -> str:
        return self._transcription

    @transcription.setter
    def transcription(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("Транскрипция должна быть строкой.")
        if len(value) > self.MAX_TRANSCRIPTION_LENGTH:
            raise ValueError(
                f"Транскрипция не может превышать {self.MAX_TRANSCRIPTION_LENGTH} символов."
            )
        self._transcription = value

    @property
    def duration_sec(self) -> int:
        return self._duration_sec

    @duration_sec.setter
    def duration_sec(self, value: int) -> None:
        if not isinstance(value, int):
            raise TypeError("Длительность должна быть целым числом.")
        if value < 0:
            raise ValueError("Длительность не может быть отрицательной.")
        if value > self.MAX_DURATION_SEC:
            raise ValueError(
                f"Длительность не может превышать {self.MAX_DURATION_SEC} секунд."
            )
        self._duration_sec = value

    def preview(self) -> str:
        mins, secs = divmod(self._duration_sec, 60)
        duration_str = f"[{mins:02d}:{secs:02d}] "
        snippet = self._transcription[:77 - len(duration_str)]
        text = duration_str + snippet
        return text + "…" if len(self._transcription) > len(snippet) else text

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["transcription"] = self._transcription
        data["duration_sec"] = self._duration_sec
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VoiceNote":
        return cls(
            title=data["title"],
            transcription=data.get("transcription", ""),
            duration_sec=data.get("duration_sec", 0),
            tags=data.get("tags", []),
            date=datetime.strptime(data["date"], DATE_FORMAT),
            note_id=data.get("note_id"),
        )


# ---------------------------------------------------------------------------
# ChecklistNote
# ---------------------------------------------------------------------------

class ChecklistNote(Note):
    """Заметка-чеклист с набором пунктов.

    Дополнительные атрибуты:
        items (list[dict]): Список пунктов вида {"text": str, "done": bool}.
    """

    MAX_ITEMS: int = 100
    MAX_ITEM_LENGTH: int = 500

    def __init__(
        self,
        title: str,
        items: list[dict[str, Any]] | None = None,
        tags: list[str] | None = None,
        date: datetime | None = None,
        note_id: str | None = None,
    ) -> None:
        super().__init__(title=title, tags=tags, date=date, note_id=note_id)
        self.items: list[dict[str, Any]] = items or []

    @property
    def note_type(self) -> str:
        return "checklist"

    @property
    def items(self) -> list[dict[str, Any]]:
        return list(self._items)

    @items.setter
    def items(self, value: list[dict[str, Any]]) -> None:
        if not isinstance(value, list):
            raise TypeError("Пункты чеклиста должны быть переданы в виде списка.")
        if len(value) > self.MAX_ITEMS:
            raise ValueError(
                f"Чеклист не может содержать более {self.MAX_ITEMS} пунктов."
            )
        cleaned: list[dict[str, Any]] = []
        for item in value:
            if not isinstance(item, dict):
                raise TypeError("Каждый пункт чеклиста должен быть словарём.")
            text = item.get("text", "")
            if not isinstance(text, str) or not text.strip():
                raise ValueError("Текст пункта чеклиста не может быть пустым.")
            if len(text) > self.MAX_ITEM_LENGTH:
                raise ValueError(
                    f"Текст пункта не может превышать {self.MAX_ITEM_LENGTH} символов."
                )
            cleaned.append({"text": text.strip(), "done": bool(item.get("done", False))})
        self._items: list[dict[str, Any]] = cleaned

    def add_item(self, text: str) -> None:
        """Добавляет новый пункт в чеклист."""
        if len(self._items) >= self.MAX_ITEMS:
            raise ValueError(f"Нельзя добавить более {self.MAX_ITEMS} пунктов.")
        text = text.strip()
        if not text:
            raise ValueError("Текст пункта не может быть пустым.")
        if len(text) > self.MAX_ITEM_LENGTH:
            raise ValueError(
                f"Текст пункта не может превышать {self.MAX_ITEM_LENGTH} символов."
            )
        self._items.append({"text": text, "done": False})

    def toggle_item(self, index: int) -> None:
        """Переключает статус выполнения пункта по индексу."""
        if not (0 <= index < len(self._items)):
            raise IndexError(f"Индекс {index} выходит за пределы чеклиста.")
        self._items[index]["done"] = not self._items[index]["done"]

    def remove_item(self, index: int) -> None:
        """Удаляет пункт чеклиста по индексу."""
        if not (0 <= index < len(self._items)):
            raise IndexError(f"Индекс {index} выходит за пределы чеклиста.")
        self._items.pop(index)

    def preview(self) -> str:
        total = len(self._items)
        done = sum(1 for i in self._items if i["done"])
        return f"[{done}/{total}] " + (self._items[0]["text"][:60] if self._items else "(пусто)")

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["items"] = list(self._items)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ChecklistNote":
        return cls(
            title=data["title"],
            items=data.get("items", []),
            tags=data.get("tags", []),
            date=datetime.strptime(data["date"], DATE_FORMAT),
            note_id=data.get("note_id"),
        )


# ---------------------------------------------------------------------------
# Фабричная функция
# ---------------------------------------------------------------------------

def note_from_dict(data: dict[str, Any]) -> Note:
    """Восстанавливает объект заметки из словаря по полю ``note_type``."""
    note_type = data.get("note_type", "text")
    mapping = {
        "text": TextNote.from_dict,
        "voice": VoiceNote.from_dict,
        "checklist": ChecklistNote.from_dict,
    }
    factory = mapping.get(note_type)
    if factory is None:
        raise ValueError(f"Неизвестный тип заметки: '{note_type}'.")
    return factory(data)
