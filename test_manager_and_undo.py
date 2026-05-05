"""
Тесты для моделей заметок (models.py).

Покрывает: TextNote, VoiceNote, ChecklistNote, note_from_dict.
Категории: позитивные, негативные, граничные случаи.
"""

import pytest
from datetime import datetime

from notebook.models import (
    TextNote,
    VoiceNote,
    ChecklistNote,
    note_from_dict,
    DATE_FORMAT,
)


# ===========================================================================
# TextNote
# ===========================================================================

class TestTextNotePositive:
    """Позитивные тесты для TextNote."""

    def test_create_minimal(self):
        """Создание заметки с минимальными данными."""
        note = TextNote(title="Заголовок")
        assert note.title == "Заголовок"
        assert note.text == ""
        assert note.tags == []
        assert isinstance(note.date, datetime)
        assert note.note_type == "text"

    def test_create_full(self):
        """Создание заметки со всеми полями."""
        dt = datetime(2024, 1, 15, 10, 30, 0)
        note = TextNote(
            title="Полная заметка",
            text="Текст заметки",
            tags=["python", "тест"],
            date=dt,
        )
        assert note.title == "Полная заметка"
        assert note.text == "Текст заметки"
        assert note.tags == ["python", "тест"]
        assert note.date == dt

    def test_note_id_is_uuid(self):
        """ID заметки является UUID."""
        note = TextNote(title="Тест")
        assert len(note.note_id) == 36
        assert note.note_id.count("-") == 4

    def test_custom_note_id(self):
        """Можно задать собственный ID."""
        note = TextNote(title="Тест", note_id="custom-id-123")
        assert note.note_id == "custom-id-123"

    def test_title_stripped(self):
        """Заголовок обрезается от пробелов."""
        note = TextNote(title="  Заголовок  ")
        assert note.title == "Заголовок"

    def test_tags_normalized_lowercase(self):
        """Теги приводятся к нижнему регистру."""
        note = TextNote(title="Тест", tags=["Python", "ТЕСТ"])
        assert note.tags == ["python", "тест"]

    def test_preview_short_text(self):
        """Превью для короткого текста не обрезается."""
        note = TextNote(title="Тест", text="Короткий текст")
        assert note.preview() == "Короткий текст"

    def test_preview_long_text(self):
        """Превью для длинного текста обрезается с многоточием."""
        note = TextNote(title="Тест", text="А" * 100)
        preview = note.preview()
        assert preview.endswith("…")
        assert len(preview) <= 80

    def test_to_dict_and_from_dict(self):
        """Сериализация и десериализация TextNote."""
        dt = datetime(2024, 3, 20, 12, 0, 0)
        note = TextNote(
            title="Тест",
            text="Содержимое",
            tags=["тег1"],
            date=dt,
            note_id="test-id",
        )
        d = note.to_dict()
        assert d["note_type"] == "text"
        assert d["title"] == "Тест"
        assert d["text"] == "Содержимое"
        assert d["tags"] == ["тег1"]

        restored = TextNote.from_dict(d)
        assert restored.title == note.title
        assert restored.text == note.text
        assert restored.tags == note.tags
        assert restored.note_id == note.note_id

    def test_has_tag(self):
        """Метод has_tag работает корректно."""
        note = TextNote(title="Тест", tags=["python", "тест"])
        assert note.has_tag("python") is True
        assert note.has_tag("PYTHON") is True  # регистронезависимо
        assert note.has_tag("java") is False

    def test_update_date(self):
        """update_date обновляет дату заметки."""
        old_dt = datetime(2020, 1, 1)
        note = TextNote(title="Тест", date=old_dt)
        note.update_date()
        assert note.date > old_dt

    def test_equality_by_id(self):
        """Две заметки с одинаковым ID равны."""
        note1 = TextNote(title="A", note_id="same-id")
        note2 = TextNote(title="B", note_id="same-id")
        assert note1 == note2

    def test_inequality_different_id(self):
        """Заметки с разными ID не равны."""
        note1 = TextNote(title="A")
        note2 = TextNote(title="A")
        assert note1 != note2


class TestTextNoteNegative:
    """Негативные тесты для TextNote."""

    def test_empty_title_raises(self):
        """Пустой заголовок вызывает ValueError."""
        with pytest.raises(ValueError, match="пустым"):
            TextNote(title="")

    def test_whitespace_title_raises(self):
        """Заголовок из пробелов вызывает ValueError."""
        with pytest.raises(ValueError):
            TextNote(title="   ")

    def test_non_string_title_raises(self):
        """Нестроковый заголовок вызывает TypeError."""
        with pytest.raises(TypeError):
            TextNote(title=123)  # type: ignore

    def test_tags_with_spaces_raises(self):
        """Тег с пробелами вызывает ValueError."""
        with pytest.raises(ValueError, match="пробел"):
            TextNote(title="Тест", tags=["тег с пробелом"])

    def test_non_list_tags_raises(self):
        """Несписковые теги вызывают TypeError."""
        with pytest.raises(TypeError):
            TextNote(title="Тест", tags="тег")  # type: ignore

    def test_non_string_tag_raises(self):
        """Нестроковый тег вызывает TypeError."""
        with pytest.raises(TypeError):
            TextNote(title="Тест", tags=[123])  # type: ignore

    def test_text_too_long_raises(self):
        """Слишком длинный текст вызывает ValueError."""
        with pytest.raises(ValueError, match="10000"):
            TextNote(title="Тест", text="А" * 10_001)

    def test_non_datetime_date_raises(self):
        """Нестроковая дата вызывает TypeError."""
        with pytest.raises(TypeError):
            TextNote(title="Тест", date="2024-01-01")  # type: ignore


class TestTextNoteBoundary:
    """Граничные случаи для TextNote."""

    def test_title_max_length(self):
        """Заголовок ровно 200 символов допустим."""
        note = TextNote(title="А" * 200)
        assert len(note.title) == 200

    def test_title_over_max_raises(self):
        """Заголовок в 201 символ вызывает ValueError."""
        with pytest.raises(ValueError):
            TextNote(title="А" * 201)

    def test_text_max_length(self):
        """Текст ровно 10 000 символов допустим."""
        note = TextNote(title="Тест", text="А" * 10_000)
        assert len(note.text) == 10_000

    def test_max_tags(self):
        """Ровно 20 тегов допустимы."""
        tags = [f"тег{i}" for i in range(20)]
        note = TextNote(title="Тест", tags=tags)
        assert len(note.tags) == 20

    def test_over_max_tags_raises(self):
        """21 тег вызывает ValueError."""
        tags = [f"тег{i}" for i in range(21)]
        with pytest.raises(ValueError):
            TextNote(title="Тест", tags=tags)

    def test_duplicate_tags_deduplicated(self):
        """Дублирующиеся теги молча удаляются (через валидатор)."""
        from notebook.validators import NoteValidator
        result = NoteValidator.validate_tags(["python", "python", "тест"])
        assert result == ["python", "тест"]

    def test_empty_text_allowed(self):
        """Пустой текст допустим."""
        note = TextNote(title="Тест", text="")
        assert note.text == ""


# ===========================================================================
# VoiceNote
# ===========================================================================

class TestVoiceNotePositive:
    """Позитивные тесты для VoiceNote."""

    def test_create_minimal(self):
        note = VoiceNote(title="Голосовая заметка")
        assert note.note_type == "voice"
        assert note.transcription == ""
        assert note.duration_sec == 0

    def test_create_full(self):
        note = VoiceNote(
            title="Встреча",
            transcription="Обсудили проект",
            duration_sec=120,
            tags=["встреча"],
        )
        assert note.transcription == "Обсудили проект"
        assert note.duration_sec == 120

    def test_preview_format(self):
        note = VoiceNote(title="Тест", transcription="Привет", duration_sec=90)
        preview = note.preview()
        assert "01:30" in preview
        assert "Привет" in preview

    def test_to_dict_from_dict(self):
        dt = datetime(2024, 5, 1, 9, 0, 0)
        note = VoiceNote(
            title="Голос",
            transcription="Текст",
            duration_sec=60,
            tags=["аудио"],
            date=dt,
            note_id="voice-id",
        )
        d = note.to_dict()
        assert d["note_type"] == "voice"
        restored = VoiceNote.from_dict(d)
        assert restored.transcription == "Текст"
        assert restored.duration_sec == 60


class TestVoiceNoteNegative:
    """Негативные тесты для VoiceNote."""

    def test_negative_duration_raises(self):
        with pytest.raises(ValueError, match="отрицательной"):
            VoiceNote(title="Тест", duration_sec=-1)

    def test_non_int_duration_raises(self):
        with pytest.raises(TypeError):
            VoiceNote(title="Тест", duration_sec="60")  # type: ignore

    def test_transcription_too_long_raises(self):
        with pytest.raises(ValueError):
            VoiceNote(title="Тест", transcription="А" * 10_001)


class TestVoiceNoteBoundary:
    """Граничные случаи для VoiceNote."""

    def test_zero_duration(self):
        note = VoiceNote(title="Тест", duration_sec=0)
        assert note.duration_sec == 0

    def test_max_duration(self):
        note = VoiceNote(title="Тест", duration_sec=10_800)
        assert note.duration_sec == 10_800

    def test_over_max_duration_raises(self):
        with pytest.raises(ValueError):
            VoiceNote(title="Тест", duration_sec=10_801)


# ===========================================================================
# ChecklistNote
# ===========================================================================

class TestChecklistNotePositive:
    """Позитивные тесты для ChecklistNote."""

    def test_create_empty(self):
        note = ChecklistNote(title="Список")
        assert note.note_type == "checklist"
        assert note.items == []

    def test_create_with_items(self):
        items = [
            {"text": "Купить молоко", "done": False},
            {"text": "Купить хлеб", "done": True},
        ]
        note = ChecklistNote(title="Покупки", items=items)
        assert len(note.items) == 2
        assert note.items[1]["done"] is True

    def test_add_item(self):
        note = ChecklistNote(title="Список")
        note.add_item("Новый пункт")
        assert len(note.items) == 1
        assert note.items[0]["text"] == "Новый пункт"
        assert note.items[0]["done"] is False

    def test_toggle_item(self):
        note = ChecklistNote(title="Список", items=[{"text": "Пункт", "done": False}])
        note.toggle_item(0)
        assert note.items[0]["done"] is True
        note.toggle_item(0)
        assert note.items[0]["done"] is False

    def test_remove_item(self):
        note = ChecklistNote(
            title="Список",
            items=[{"text": "A", "done": False}, {"text": "B", "done": False}],
        )
        note.remove_item(0)
        assert len(note.items) == 1
        assert note.items[0]["text"] == "B"

    def test_preview_format(self):
        note = ChecklistNote(
            title="Список",
            items=[
                {"text": "Пункт 1", "done": True},
                {"text": "Пункт 2", "done": False},
            ],
        )
        preview = note.preview()
        assert "1/2" in preview

    def test_to_dict_from_dict(self):
        dt = datetime(2024, 6, 1, 8, 0, 0)
        note = ChecklistNote(
            title="Задачи",
            items=[{"text": "Задача 1", "done": False}],
            tags=["работа"],
            date=dt,
            note_id="check-id",
        )
        d = note.to_dict()
        assert d["note_type"] == "checklist"
        restored = ChecklistNote.from_dict(d)
        assert len(restored.items) == 1
        assert restored.items[0]["text"] == "Задача 1"


class TestChecklistNoteNegative:
    """Негативные тесты для ChecklistNote."""

    def test_add_empty_item_raises(self):
        note = ChecklistNote(title="Список")
        with pytest.raises(ValueError, match="пустым"):
            note.add_item("")

    def test_toggle_invalid_index_raises(self):
        note = ChecklistNote(title="Список")
        with pytest.raises(IndexError):
            note.toggle_item(0)

    def test_remove_invalid_index_raises(self):
        note = ChecklistNote(title="Список", items=[{"text": "Пункт", "done": False}])
        with pytest.raises(IndexError):
            note.remove_item(5)

    def test_non_list_items_raises(self):
        with pytest.raises(TypeError):
            ChecklistNote(title="Список", items="пункт")  # type: ignore

    def test_item_without_text_raises(self):
        with pytest.raises(ValueError):
            ChecklistNote(title="Список", items=[{"text": "", "done": False}])


class TestChecklistNoteBoundary:
    """Граничные случаи для ChecklistNote."""

    def test_max_items(self):
        items = [{"text": f"Пункт {i}", "done": False} for i in range(100)]
        note = ChecklistNote(title="Список", items=items)
        assert len(note.items) == 100

    def test_over_max_items_raises(self):
        items = [{"text": f"Пункт {i}", "done": False} for i in range(101)]
        with pytest.raises(ValueError):
            ChecklistNote(title="Список", items=items)

    def test_add_item_to_full_raises(self):
        items = [{"text": f"Пункт {i}", "done": False} for i in range(100)]
        note = ChecklistNote(title="Список", items=items)
        with pytest.raises(ValueError):
            note.add_item("Лишний пункт")


# ===========================================================================
# note_from_dict (фабричная функция)
# ===========================================================================

class TestNoteFromDict:
    """Тесты фабричной функции note_from_dict."""

    def test_text_note(self):
        d = {
            "note_type": "text",
            "note_id": "id1",
            "title": "Тест",
            "text": "Содержимое",
            "tags": [],
            "date": "2024-01-01 00:00:00",
        }
        note = note_from_dict(d)
        assert isinstance(note, TextNote)

    def test_voice_note(self):
        d = {
            "note_type": "voice",
            "note_id": "id2",
            "title": "Голос",
            "transcription": "",
            "duration_sec": 30,
            "tags": [],
            "date": "2024-01-01 00:00:00",
        }
        note = note_from_dict(d)
        assert isinstance(note, VoiceNote)

    def test_checklist_note(self):
        d = {
            "note_type": "checklist",
            "note_id": "id3",
            "title": "Список",
            "items": [],
            "tags": [],
            "date": "2024-01-01 00:00:00",
        }
        note = note_from_dict(d)
        assert isinstance(note, ChecklistNote)

    def test_unknown_type_raises(self):
        d = {
            "note_type": "unknown",
            "note_id": "id4",
            "title": "Тест",
            "date": "2024-01-01 00:00:00",
        }
        with pytest.raises(ValueError, match="Неизвестный тип"):
            note_from_dict(d)
