"""
Тесты для NoteValidator (validators.py).

Категории: позитивные, негативные, граничные случаи.
"""

import pytest
from notebook.validators import NoteValidator


class TestValidateTitle:
    """Тесты валидации заголовка."""

    def test_valid_title(self):
        assert NoteValidator.validate_title("Заголовок") == "Заголовок"

    def test_title_stripped(self):
        assert NoteValidator.validate_title("  Заголовок  ") == "Заголовок"

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            NoteValidator.validate_title("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError):
            NoteValidator.validate_title("   ")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_title(42)  # type: ignore

    def test_max_length(self):
        result = NoteValidator.validate_title("А" * 200)
        assert len(result) == 200

    def test_over_max_length_raises(self):
        with pytest.raises(ValueError, match="200"):
            NoteValidator.validate_title("А" * 201)


class TestValidateTags:
    """Тесты валидации тегов."""

    def test_valid_tags(self):
        result = NoteValidator.validate_tags(["python", "тест"])
        assert result == ["python", "тест"]

    def test_tags_normalized_lowercase(self):
        result = NoteValidator.validate_tags(["Python", "ТЕСТ"])
        assert result == ["python", "тест"]

    def test_tags_stripped(self):
        result = NoteValidator.validate_tags(["  python  "])
        assert result == ["python"]

    def test_empty_list(self):
        assert NoteValidator.validate_tags([]) == []

    def test_duplicates_removed(self):
        result = NoteValidator.validate_tags(["python", "python", "тест"])
        assert result == ["python", "тест"]

    def test_non_list_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_tags("python")  # type: ignore

    def test_empty_tag_raises(self):
        with pytest.raises(ValueError, match="пустой"):
            NoteValidator.validate_tags([""])

    def test_tag_with_space_raises(self):
        with pytest.raises(ValueError, match="недопустимые"):
            NoteValidator.validate_tags(["тег с пробелом"])

    def test_non_string_tag_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_tags([123])  # type: ignore

    def test_max_tags(self):
        tags = [f"тег{i}" for i in range(20)]
        result = NoteValidator.validate_tags(tags)
        assert len(result) == 20

    def test_over_max_tags_raises(self):
        tags = [f"тег{i}" for i in range(21)]
        with pytest.raises(ValueError, match="20"):
            NoteValidator.validate_tags(tags)

    def test_tag_with_hyphen_allowed(self):
        result = NoteValidator.validate_tags(["тег-один"])
        assert result == ["тег-один"]

    def test_tag_with_underscore_allowed(self):
        result = NoteValidator.validate_tags(["тег_один"])
        assert result == ["тег_один"]


class TestValidateDateString:
    """Тесты валидации строки даты."""

    def test_valid_date(self):
        from datetime import datetime
        dt = NoteValidator.validate_date_string("2024-01-15 10:30:00")
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 15

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="формат"):
            NoteValidator.validate_date_string("15.01.2024")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_date_string(20240115)  # type: ignore


class TestValidateNoteType:
    """Тесты валидации типа заметки."""

    def test_valid_text(self):
        assert NoteValidator.validate_note_type("text") == "text"

    def test_valid_voice(self):
        assert NoteValidator.validate_note_type("voice") == "voice"

    def test_valid_checklist(self):
        assert NoteValidator.validate_note_type("checklist") == "checklist"

    def test_case_insensitive(self):
        assert NoteValidator.validate_note_type("TEXT") == "text"

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Неизвестный"):
            NoteValidator.validate_note_type("image")

    def test_non_string_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_note_type(1)  # type: ignore


class TestValidateDuration:
    """Тесты валидации длительности."""

    def test_valid_duration(self):
        assert NoteValidator.validate_duration(120) == 120

    def test_zero_duration(self):
        assert NoteValidator.validate_duration(0) == 0

    def test_max_duration(self):
        assert NoteValidator.validate_duration(10_800) == 10_800

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="отрицательной"):
            NoteValidator.validate_duration(-1)

    def test_over_max_raises(self):
        with pytest.raises(ValueError):
            NoteValidator.validate_duration(10_801)

    def test_string_convertible(self):
        assert NoteValidator.validate_duration("60") == 60  # type: ignore

    def test_non_numeric_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_duration("abc")  # type: ignore


class TestValidateChecklistItems:
    """Тесты валидации пунктов чеклиста."""

    def test_valid_items(self):
        items = [{"text": "Пункт 1", "done": False}]
        result = NoteValidator.validate_checklist_items(items)
        assert len(result) == 1
        assert result[0]["text"] == "Пункт 1"

    def test_empty_list(self):
        assert NoteValidator.validate_checklist_items([]) == []

    def test_done_defaults_to_false(self):
        items = [{"text": "Пункт"}]
        result = NoteValidator.validate_checklist_items(items)
        assert result[0]["done"] is False

    def test_non_list_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_checklist_items("пункт")  # type: ignore

    def test_empty_text_raises(self):
        with pytest.raises(ValueError):
            NoteValidator.validate_checklist_items([{"text": "", "done": False}])

    def test_non_dict_item_raises(self):
        with pytest.raises(TypeError):
            NoteValidator.validate_checklist_items(["строка"])  # type: ignore

    def test_max_items(self):
        items = [{"text": f"Пункт {i}", "done": False} for i in range(100)]
        result = NoteValidator.validate_checklist_items(items)
        assert len(result) == 100

    def test_over_max_items_raises(self):
        items = [{"text": f"Пункт {i}", "done": False} for i in range(101)]
        with pytest.raises(ValueError, match="100"):
            NoteValidator.validate_checklist_items(items)

    def test_text_stripped(self):
        items = [{"text": "  Пункт  ", "done": False}]
        result = NoteValidator.validate_checklist_items(items)
        assert result[0]["text"] == "Пункт"
