"""
Стек отмены действий (UndoStack) для Notebook Organizer.

Каждая операция сохраняется как команда с методами execute() и undo().
Стек поддерживает ограниченную глубину истории (по умолчанию 50 операций).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from copy import deepcopy
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .models import Note


# ---------------------------------------------------------------------------
# Абстрактная команда
# ---------------------------------------------------------------------------

class Command(ABC):
    """Абстрактный базовый класс команды (паттерн «Команда»)."""

    @abstractmethod
    def execute(self) -> None:
        """Выполнить команду."""

    @abstractmethod
    def undo(self) -> None:
        """Отменить команду."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Человекочитаемое описание команды."""


# ---------------------------------------------------------------------------
# Конкретные команды
# ---------------------------------------------------------------------------

class AddNoteCommand(Command):
    """Команда добавления заметки."""

    def __init__(self, storage: list["Note"], note: "Note") -> None:
        self._storage = storage
        self._note = deepcopy(note)

    def execute(self) -> None:
        self._storage.append(deepcopy(self._note))

    def undo(self) -> None:
        # Удаляем последнюю добавленную заметку с таким же ID
        for i, n in enumerate(self._storage):
            if n.note_id == self._note.note_id:
                self._storage.pop(i)
                return

    @property
    def description(self) -> str:
        return f"Добавление заметки: «{self._note.title}»"


class DeleteNoteCommand(Command):
    """Команда удаления заметки."""

    def __init__(self, storage: list["Note"], note: "Note") -> None:
        self._storage = storage
        self._note = deepcopy(note)

    def execute(self) -> None:
        for i, n in enumerate(self._storage):
            if n.note_id == self._note.note_id:
                self._storage.pop(i)
                return

    def undo(self) -> None:
        self._storage.append(deepcopy(self._note))

    @property
    def description(self) -> str:
        return f"Удаление заметки: «{self._note.title}»"


class UpdateNoteCommand(Command):
    """Команда обновления заметки (хранит снимок до и после)."""

    def __init__(
        self,
        storage: list["Note"],
        old_note: "Note",
        new_note: "Note",
    ) -> None:
        self._storage = storage
        self._old = deepcopy(old_note)
        self._new = deepcopy(new_note)

    def execute(self) -> None:
        self._replace(self._old.note_id, self._new)

    def undo(self) -> None:
        self._replace(self._new.note_id, self._old)

    def _replace(self, target_id: str, replacement: "Note") -> None:
        for i, n in enumerate(self._storage):
            if n.note_id == target_id:
                self._storage[i] = deepcopy(replacement)
                return

    @property
    def description(self) -> str:
        return f"Редактирование заметки: «{self._old.title}» → «{self._new.title}»"


# ---------------------------------------------------------------------------
# Стек отмены
# ---------------------------------------------------------------------------

class UndoStack:
    """Стек для хранения истории команд и поддержки операции отмены.

    Атрибуты:
        max_size (int): Максимальное количество хранимых команд.
    """

    DEFAULT_MAX_SIZE: int = 50

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        if max_size < 1:
            raise ValueError("Размер стека должен быть не менее 1.")
        self._max_size: int = max_size
        self._stack: deque[Command] = deque(maxlen=max_size)

    # ------------------------------------------------------------------
    # Публичный интерфейс
    # ------------------------------------------------------------------

    def push(self, command: Command) -> None:
        """Добавляет команду в стек (без выполнения)."""
        if not isinstance(command, Command):
            raise TypeError("Ожидается объект типа Command.")
        self._stack.append(command)

    def undo(self) -> str:
        """Отменяет последнюю команду и возвращает её описание.

        Raises:
            IndexError: Если стек пуст.
        """
        if not self._stack:
            raise IndexError("История действий пуста — нечего отменять.")
        command = self._stack.pop()
        command.undo()
        return command.description

    def peek(self) -> Command | None:
        """Возвращает последнюю команду без удаления из стека."""
        return self._stack[-1] if self._stack else None

    def clear(self) -> None:
        """Очищает стек."""
        self._stack.clear()

    # ------------------------------------------------------------------
    # Вспомогательные методы
    # ------------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        """True, если стек пуст."""
        return len(self._stack) == 0

    @property
    def size(self) -> int:
        """Текущее количество команд в стеке."""
        return len(self._stack)

    @property
    def max_size(self) -> int:
        return self._max_size

    def history(self) -> list[str]:
        """Возвращает список описаний команд от старых к новым."""
        return [cmd.description for cmd in self._stack]

    def __len__(self) -> int:
        return len(self._stack)

    def __repr__(self) -> str:
        return f"UndoStack(size={self.size}/{self._max_size})"
