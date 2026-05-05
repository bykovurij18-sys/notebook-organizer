"""
Тесты для NoteManager, UndoStack, NoteFilter и JSONStorage.

Категории: позитивные, негативные, граничные случаи.
"""

import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

from notebook.manager import NoteManager, NoteNotFoundError
from notebook.models import TextNote, VoiceNote, ChecklistNote
from notebook.undo_stack import UndoStack, AddNoteCommand
from notebook.filters import NoteFilter
from notebook.storage import JSONStorage, StorageError


# ===========================================================================
# Фикстуры
# ===========================================================================

@pytest.fixture
def manager():
    """NoteManager с временным хранилищем."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        tmp_path = f.name
    storage = JSONStorage(tmp_path)
    mgr = NoteManager(storage=storage)
    yield mgr
    # Очистка
    storage.delete_file()


@pytest.fixture
def populated_manager(manager):
    """NoteManager с тремя заметками."""
    manager.create_text_note("Заметка 1", text="Текст 1", tags=["python", "работа"])
    manager.create_text_note("Заметка 2", text="Текст 2", tags=["личное"])
    manager.create_voice_note("Голос 1", transcription="Транскрипция", duration_sec=60, tags=["python"])
    return manager


# ===========================================================================
# NoteManager — CRUD
# ===========================================================================

class TestNoteManagerCreate:
    """Тесты создания заметок."""

    def test_create_text_note(self, manager):
        note = manager.create_text_note("Тест", text="Содержимое", tags=["тег"])
        assert isinstance(note, TextNote)
        assert note.title == "Тест"
        assert manager.count() == 1

    def test_create_voice_note(self, manager):
        note = manager.create_voice_note("Голос", transcription="Текст", duration_sec=30)
        assert isinstance(note, VoiceNote)
        assert manager.count() == 1

    def test_create_checklist_note(self, manager):
        items = [{"text": "Пункт 1", "done": False}]
        note = manager.create_checklist_note("Список", items=items)
        assert isinstance(note, ChecklistNote)
        assert manager.count() == 1

    def test_add_note_directly(self, manager):
        note = TextNote(title="Прямое добавление")
        added = manager.add_note(note)
        assert added.note_id == note.note_id
        assert manager.count() == 1

    def test_duplicate_id_raises(self, manager):
        note = TextNote(title="Тест", note_id="duplicate-id")
        manager.add_note(note)
        with pytest.raises(ValueError, match="уже существует"):
            manager.add_note(TextNote(title="Другой", note_id="duplicate-id"))

    def test_empty_title_raises(self, manager):
        with pytest.raises(ValueError):
            manager.create_text_note("")

    def test_invalid_tags_raises(self, manager):
        with pytest.raises(ValueError):
            manager.create_text_note("Тест", tags=["тег с пробелом"])


class TestNoteManagerRead:
    """Тесты чтения заметок."""

    def test_get_all_empty(self, manager):
        assert manager.get_all() == []

    def test_get_all_returns_copy(self, populated_manager):
        notes = populated_manager.get_all()
        assert len(notes) == 3
        notes.clear()  # изменение копии не влияет на оригинал
        assert populated_manager.count() == 3

    def test_get_by_id(self, manager):
        note = manager.create_text_note("Поиск по ID")
        found = manager.get_by_id(note.note_id)
        assert found.title == "Поиск по ID"

    def test_get_by_id_not_found(self, manager):
        with pytest.raises(NoteNotFoundError):
            manager.get_by_id("несуществующий-id")

    def test_count(self, populated_manager):
        assert populated_manager.count() == 3


class TestNoteManagerUpdate:
    """Тесты обновления заметок."""

    def test_update_title(self, manager):
        note = manager.create_text_note("Старый заголовок")
        updated = manager.update_note(note.note_id, title="Новый заголовок")
        assert updated.title == "Новый заголовок"

    def test_update_text(self, manager):
        note = manager.create_text_note("Тест", text="Старый текст")
        updated = manager.update_note(note.note_id, text="Новый текст")
        assert isinstance(updated, TextNote)
        assert updated.text == "Новый текст"

    def test_update_tags(self, manager):
        note = manager.create_text_note("Тест", tags=["старый"])
        updated = manager.update_note(note.note_id, tags=["новый", "тег"])
        assert updated.tags == ["новый", "тег"]

    def test_update_voice_note_fields(self, manager):
        note = manager.create_voice_note("Голос", duration_sec=30)
        updated = manager.update_note(note.note_id, duration_sec=90, transcription="Новый текст")
        assert isinstance(updated, VoiceNote)
        assert updated.duration_sec == 90
        assert updated.transcription == "Новый текст"

    def test_update_date_refreshed(self, manager):
        old_dt = datetime(2020, 1, 1)
        note = TextNote(title="Тест", date=old_dt)
        manager.add_note(note)
        updated = manager.update_note(note.note_id, title="Обновлён")
        assert updated.date > old_dt

    def test_update_nonexistent_raises(self, manager):
        with pytest.raises(NoteNotFoundError):
            manager.update_note("несуществующий-id", title="Тест")

    def test_update_invalid_title_raises(self, manager):
        note = manager.create_text_note("Тест")
        with pytest.raises(ValueError):
            manager.update_note(note.note_id, title="")


class TestNoteManagerDelete:
    """Тесты удаления заметок."""

    def test_delete_note(self, manager):
        note = manager.create_text_note("Удалить")
        deleted = manager.delete_note(note.note_id)
        assert deleted.title == "Удалить"
        assert manager.count() == 0

    def test_delete_nonexistent_raises(self, manager):
        with pytest.raises(NoteNotFoundError):
            manager.delete_note("несуществующий-id")

    def test_delete_all(self, populated_manager):
        count = populated_manager.delete_all()
        assert count == 3
        assert populated_manager.count() == 0

    def test_delete_reduces_count(self, populated_manager):
        notes = populated_manager.get_all()
        populated_manager.delete_note(notes[0].note_id)
        assert populated_manager.count() == 2


# ===========================================================================
# UndoStack
# ===========================================================================

class TestUndoStack:
    """Тесты стека отмены."""

    def test_undo_add(self, manager):
        """Отмена добавления удаляет заметку."""
        manager.create_text_note("Тест")
        assert manager.count() == 1
        manager.undo()
        assert manager.count() == 0

    def test_undo_delete(self, manager):
        """Отмена удаления восстанавливает заметку."""
        note = manager.create_text_note("Тест")
        manager.undo()  # отменяем добавление
        manager.add_note(note)  # добавляем снова
        manager.delete_note(note.note_id)
        assert manager.count() == 0
        manager.undo()
        assert manager.count() == 1

    def test_undo_update(self, manager):
        """Отмена обновления восстанавливает прежние данные."""
        note = manager.create_text_note("Оригинал", text="Старый текст")
        manager.update_note(note.note_id, title="Изменённый")
        manager.undo()
        restored = manager.get_by_id(note.note_id)
        assert restored.title == "Оригинал"

    def test_undo_empty_raises(self, manager):
        """Отмена при пустой истории вызывает IndexError."""
        with pytest.raises(IndexError, match="пуста"):
            manager.undo()

    def test_can_undo_property(self, manager):
        assert manager.can_undo is False
        manager.create_text_note("Тест")
        assert manager.can_undo is True
        manager.undo()
        assert manager.can_undo is False

    def test_undo_history(self, manager):
        manager.create_text_note("Заметка 1")
        manager.create_text_note("Заметка 2")
        history = manager.undo_history()
        assert len(history) == 2
        assert "Заметка 1" in history[0]
        assert "Заметка 2" in history[1]

    def test_undo_stack_max_size(self):
        """Стек ограничен максимальным размером."""
        stack = UndoStack(max_size=3)
        notes: list = []
        for i in range(5):
            note = TextNote(title=f"Заметка {i}")
            cmd = AddNoteCommand(notes, note)
            cmd.execute()
            stack.push(cmd)
        assert stack.size == 3  # старые команды вытеснены

    def test_undo_stack_invalid_size(self):
        with pytest.raises(ValueError):
            UndoStack(max_size=0)

    def test_undo_stack_clear(self, manager):
        manager.create_text_note("Тест")
        assert manager.can_undo is True
        manager.delete_all()  # вызывает clear()
        assert manager.can_undo is False


# ===========================================================================
# NoteFilter
# ===========================================================================

class TestNoteFilter:
    """Тесты фильтрации заметок."""

    @pytest.fixture
    def notes(self):
        dt1 = datetime(2024, 1, 10, 10, 0, 0)
        dt2 = datetime(2024, 2, 15, 12, 0, 0)
        dt3 = datetime(2024, 3, 20, 8, 0, 0)
        return [
            TextNote(title="Python заметка", tags=["python", "работа"], date=dt1),
            TextNote(title="Личная заметка", tags=["личное"], date=dt2),
            VoiceNote(title="Голосовая", tags=["python", "аудио"], date=dt3),
        ]

    def test_filter_by_tag(self, notes):
        result = NoteFilter.by_tag(notes, "python")
        assert len(result) == 2

    def test_filter_by_tag_case_insensitive(self, notes):
        result = NoteFilter.by_tag(notes, "PYTHON")
        assert len(result) == 2

    def test_filter_by_tag_no_match(self, notes):
        result = NoteFilter.by_tag(notes, "java")
        assert result == []

    def test_filter_by_tags_all(self, notes):
        result = NoteFilter.by_tags_all(notes, ["python", "работа"])
        assert len(result) == 1
        assert result[0].title == "Python заметка"

    def test_filter_by_tags_any(self, notes):
        result = NoteFilter.by_tags_any(notes, ["личное", "аудио"])
        assert len(result) == 2

    def test_filter_by_date(self, notes):
        result = NoteFilter.by_date(notes, datetime(2024, 1, 10).date())
        assert len(result) == 1
        assert result[0].title == "Python заметка"

    def test_filter_by_date_range(self, notes):
        start = datetime(2024, 1, 1)
        end = datetime(2024, 2, 28)
        result = NoteFilter.by_date_range(notes, start, end)
        assert len(result) == 2

    def test_filter_by_date_range_no_start(self, notes):
        end = datetime(2024, 1, 31)
        result = NoteFilter.by_date_range(notes, end=end)
        assert len(result) == 1

    def test_filter_by_type(self, notes):
        result = NoteFilter.by_type(notes, "voice")
        assert len(result) == 1
        assert result[0].title == "Голосовая"

    def test_filter_by_title(self, notes):
        result = NoteFilter.by_title(notes, "python")
        assert len(result) == 1

    def test_filter_by_title_case_insensitive(self, notes):
        result = NoteFilter.by_title(notes, "PYTHON")
        assert len(result) == 1

    def test_sort_by_date_descending(self, notes):
        sorted_notes = NoteFilter.sort_by_date(notes, descending=True)
        assert sorted_notes[0].title == "Голосовая"
        assert sorted_notes[-1].title == "Python заметка"

    def test_sort_by_date_ascending(self, notes):
        sorted_notes = NoteFilter.sort_by_date(notes, descending=False)
        assert sorted_notes[0].title == "Python заметка"

    def test_sort_by_title(self, notes):
        sorted_notes = NoteFilter.sort_by_title(notes)
        # Проверяем порядок: "Голосовая", "Личная заметка", "Python заметка"
        titles = [n.title for n in sorted_notes]
        assert titles == sorted(titles, key=lambda t: t.lower())

    def test_filter_empty_list(self):
        assert NoteFilter.by_tag([], "тег") == []
        assert NoteFilter.by_date([], datetime.now().date()) == []


# ===========================================================================
# JSONStorage
# ===========================================================================

class TestJSONStorage:
    """Тесты JSON-хранилища."""

    @pytest.fixture
    def storage(self, tmp_path):
        return JSONStorage(tmp_path / "test_notes.json")

    def test_save_and_load(self, storage):
        notes = [
            TextNote(title="Заметка 1", text="Текст 1"),
            VoiceNote(title="Голос 1", duration_sec=30),
        ]
        storage.save(notes)
        loaded = storage.load()
        assert len(loaded) == 2
        assert loaded[0].title == "Заметка 1"
        assert loaded[1].title == "Голос 1"

    def test_load_empty_if_no_file(self, tmp_path):
        storage = JSONStorage(tmp_path / "nonexistent.json")
        assert storage.load() == []

    def test_save_creates_file(self, storage):
        storage.save([TextNote(title="Тест")])
        assert storage.exists()

    def test_backup_created_on_save(self, storage):
        storage.save([TextNote(title="Первое сохранение")])
        storage.save([TextNote(title="Второе сохранение")])
        backup = storage.path.with_suffix(".bak")
        assert backup.exists()

    def test_load_invalid_json_raises(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("это не JSON", encoding="utf-8")
        storage = JSONStorage(bad_file)
        with pytest.raises(StorageError, match="некорректный JSON"):
            storage.load()

    def test_load_wrong_structure_raises(self, tmp_path):
        bad_file = tmp_path / "bad_structure.json"
        bad_file.write_text('{"data": []}', encoding="utf-8")
        storage = JSONStorage(bad_file)
        with pytest.raises(StorageError, match="неожиданную структуру"):
            storage.load()

    def test_save_all_types(self, storage):
        notes = [
            TextNote(title="Текст"),
            VoiceNote(title="Голос"),
            ChecklistNote(title="Список", items=[{"text": "Пункт", "done": False}]),
        ]
        storage.save(notes)
        loaded = storage.load()
        assert len(loaded) == 3
        types = {n.note_type for n in loaded}
        assert types == {"text", "voice", "checklist"}

    def test_save_empty_list(self, storage):
        storage.save([])
        loaded = storage.load()
        assert loaded == []

    def test_delete_file(self, storage):
        storage.save([TextNote(title="Тест")])
        assert storage.exists()
        storage.delete_file()
        assert not storage.exists()

    def test_round_trip_preserves_data(self, storage):
        """Данные не теряются при сохранении и загрузке."""
        dt = datetime(2024, 7, 4, 14, 30, 0)
        original = TextNote(
            title="Точный тест",
            text="Содержимое",
            tags=["тег1", "тег2"],
            date=dt,
            note_id="precise-id",
        )
        storage.save([original])
        loaded = storage.load()
        restored = loaded[0]
        assert restored.note_id == original.note_id
        assert restored.title == original.title
        assert isinstance(restored, TextNote)
        assert restored.text == original.text
        assert restored.tags == original.tags
        assert restored.date == original.date


# ===========================================================================
# NoteManager — интеграционные тесты
# ===========================================================================

class TestNoteManagerIntegration:
    """Интеграционные тесты NoteManager."""

    def test_save_and_reload(self, manager):
        """Данные сохраняются и восстанавливаются корректно."""
        manager.create_text_note("Заметка 1", text="Текст 1", tags=["тест"])
        manager.create_voice_note("Голос 1", duration_sec=45)
        manager.save()

        new_manager = NoteManager(storage=JSONStorage(manager.storage_path))
        new_manager.load()
        assert new_manager.count() == 2

    def test_filter_after_crud(self, manager):
        """Фильтрация работает корректно после CRUD-операций."""
        manager.create_text_note("Python", tags=["python"])
        manager.create_text_note("Java", tags=["java"])
        manager.create_text_note("Python 2", tags=["python"])

        python_notes = manager.filter_by_tag("python")
        assert len(python_notes) == 2

        manager.delete_note(python_notes[0].note_id)
        python_notes_after = manager.filter_by_tag("python")
        assert len(python_notes_after) == 1

    def test_multiple_undos(self, manager):
        """Несколько последовательных отмен работают корректно."""
        manager.create_text_note("Заметка 1")
        manager.create_text_note("Заметка 2")
        manager.create_text_note("Заметка 3")
        assert manager.count() == 3

        manager.undo()
        assert manager.count() == 2
        manager.undo()
        assert manager.count() == 1
        manager.undo()
        assert manager.count() == 0

    def test_sorted_by_date(self, manager):
        """Сортировка по дате возвращает заметки в правильном порядке."""
        dt_old = datetime(2023, 1, 1)
        dt_new = datetime(2024, 1, 1)
        manager.add_note(TextNote(title="Старая", date=dt_old))
        manager.add_note(TextNote(title="Новая", date=dt_new))

        sorted_desc = manager.sorted_by_date(descending=True)
        assert sorted_desc[0].title == "Новая"

        sorted_asc = manager.sorted_by_date(descending=False)
        assert sorted_asc[0].title == "Старая"
