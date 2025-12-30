"""
Tests for JARVIS Reminders module.
"""

import pytest
import tempfile
import os
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestReminderDatabase:
    """Tests for ReminderDatabase class."""

    @pytest.fixture
    def db(self):
        """Create a temporary database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        from modules.reminders import ReminderDatabase
        database = ReminderDatabase(db_path)

        yield database

        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_add_reminder(self, db):
        """Test adding a reminder."""
        from modules.reminders import Reminder

        reminder = Reminder(
            id=None,
            message="Test reminder",
            trigger_time=datetime.now() + timedelta(hours=1)
        )
        reminder_id = db.add_reminder(reminder)

        assert reminder_id > 0

    def test_get_pending_reminders(self, db):
        """Test getting pending reminders."""
        from modules.reminders import Reminder

        reminder = Reminder(
            id=None,
            message="Test reminder",
            trigger_time=datetime.now() + timedelta(hours=1)
        )
        db.add_reminder(reminder)

        pending = db.get_pending_reminders()
        assert len(pending) == 1
        assert pending[0].message == "Test reminder"

    def test_get_due_reminders(self, db):
        """Test getting due reminders."""
        from modules.reminders import Reminder

        # Past reminder (due)
        past_reminder = Reminder(
            id=None,
            message="Past reminder",
            trigger_time=datetime.now() - timedelta(minutes=5)
        )
        db.add_reminder(past_reminder)

        # Future reminder (not due)
        future_reminder = Reminder(
            id=None,
            message="Future reminder",
            trigger_time=datetime.now() + timedelta(hours=1)
        )
        db.add_reminder(future_reminder)

        due = db.get_due_reminders()
        assert len(due) == 1
        assert due[0].message == "Past reminder"

    def test_mark_triggered(self, db):
        """Test marking reminder as triggered."""
        from modules.reminders import Reminder

        reminder = Reminder(
            id=None,
            message="Test reminder",
            trigger_time=datetime.now() - timedelta(minutes=1)
        )
        reminder_id = db.add_reminder(reminder)
        db.mark_triggered(reminder_id)

        pending = db.get_pending_reminders()
        assert len(pending) == 0

    def test_delete_reminder(self, db):
        """Test deleting a reminder."""
        from modules.reminders import Reminder

        reminder = Reminder(
            id=None,
            message="To delete",
            trigger_time=datetime.now() + timedelta(hours=1)
        )
        reminder_id = db.add_reminder(reminder)

        assert db.delete_reminder(reminder_id)
        assert len(db.get_pending_reminders()) == 0

    def test_voice_notes(self, db):
        """Test voice notes functionality."""
        note_id = db.add_voice_note("Test note content", ["tag1", "tag2"])
        assert note_id > 0

        notes = db.get_voice_notes()
        assert len(notes) == 1
        assert notes[0]["content"] == "Test note content"
        assert "tag1" in notes[0]["tags"]

    def test_search_voice_notes(self, db):
        """Test searching voice notes."""
        db.add_voice_note("Meeting notes about project", ["meeting"])
        db.add_voice_note("Shopping list", ["personal"])

        results = db.search_voice_notes("project")
        assert len(results) == 1
        assert "project" in results[0]["content"]


class TestReminderManager:
    """Tests for ReminderManager class."""

    @pytest.fixture
    def manager(self):
        """Create a reminder manager with temp database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        from modules.reminders import ReminderManager
        mgr = ReminderManager(db_path=db_path, check_interval=0.1)

        yield mgr

        mgr.stop()
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_parse_reminder_minutes(self, manager):
        """Test parsing 'en X minutos' format."""
        is_reminder, response = manager.parse_and_create_reminder(
            "recuérdame en 30 minutos revisar el correo"
        )

        assert is_reminder
        assert "30 minutos" in response or "correo" in response

    def test_parse_reminder_hours(self, manager):
        """Test parsing 'en X horas' format."""
        is_reminder, response = manager.parse_and_create_reminder(
            "recuérdame en 2 horas llamar a Juan"
        )

        assert is_reminder
        assert response is not None

    def test_parse_reminder_at_time(self, manager):
        """Test parsing 'a las HH:MM' format."""
        is_reminder, response = manager.parse_and_create_reminder(
            "recuérdame a las 15:30 que tengo reunión"
        )

        assert is_reminder
        assert response is not None

    def test_parse_reminder_variations(self, manager):
        """Test different reminder phrase variations."""
        phrases = [
            "recuérdame que debo comprar leche",
            "pon un recordatorio para revisar el informe",
            "avísame cuando termine la descarga",
        ]

        for phrase in phrases:
            is_reminder, response = manager.parse_and_create_reminder(phrase)
            assert is_reminder, f"Should recognize: {phrase}"

    def test_parse_note(self, manager):
        """Test parsing voice notes."""
        phrases = [
            "anota que mañana es el cumpleaños de María",
            "toma nota de que el cliente necesita el reporte",
            "guarda esta nota: ideas para el proyecto",
        ]

        for phrase in phrases:
            is_note, response = manager.parse_and_create_note(phrase)
            assert is_note, f"Should recognize: {phrase}"

    def test_work_session_tracking(self, manager):
        """Test work session tracking."""
        manager.start()
        time.sleep(0.2)

        duration = manager.get_work_duration()
        assert duration is not None
        assert duration.total_seconds() >= 0

    def test_reset_work_session(self, manager):
        """Test resetting work session."""
        manager.start()
        time.sleep(0.1)

        manager.reset_work_session()
        duration = manager.get_work_duration()

        assert duration.total_seconds() < 1

    def test_pending_reminders_summary(self, manager):
        """Test getting pending reminders summary."""
        from modules.reminders import Reminder

        manager.db.add_reminder(Reminder(
            id=None,
            message="Test reminder 1",
            trigger_time=datetime.now() + timedelta(hours=1)
        ))
        manager.db.add_reminder(Reminder(
            id=None,
            message="Test reminder 2",
            trigger_time=datetime.now() + timedelta(hours=2)
        ))

        summary = manager.get_pending_reminders_summary()
        assert "2 recordatorios" in summary

    def test_cancel_reminder(self, manager):
        """Test canceling a reminder."""
        from modules.reminders import Reminder

        manager.db.add_reminder(Reminder(
            id=None,
            message="Reminder about meeting",
            trigger_time=datetime.now() + timedelta(hours=1)
        ))

        result = manager.cancel_reminder("meeting")
        assert "cancelado" in result.lower()

    def test_reminder_callback(self, manager):
        """Test reminder callback is called."""
        from modules.reminders import Reminder

        reminders_triggered = []

        def on_reminder(msg):
            reminders_triggered.append(msg)

        manager.on_reminder = on_reminder

        # Add past reminder
        manager.db.add_reminder(Reminder(
            id=None,
            message="Past reminder",
            trigger_time=datetime.now() - timedelta(minutes=1)
        ))

        # Process reminders
        manager._process_due_reminders()

        assert len(reminders_triggered) == 1


class TestReminderQueryHandler:
    """Tests for ReminderQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a reminder query handler."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        from modules.reminders import ReminderManager, ReminderQueryHandler
        manager = ReminderManager(db_path=db_path)
        handler = ReminderQueryHandler(manager)

        yield handler

        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_list_reminders_query(self, handler):
        """Test listing reminders query."""
        queries = [
            "qué recordatorios tengo",
            "mis recordatorios",
            "recordatorios pendientes",
        ]

        for query in queries:
            is_handled, response = handler.process_input(query)
            assert is_handled, f"Should handle: {query}"

    def test_work_time_query(self, handler):
        """Test work time query."""
        handler.manager.start()
        time.sleep(0.1)

        queries = [
            "cuánto llevo trabajando",
            "cuánto llevo en la sesión",
        ]

        for query in queries:
            is_handled, response = handler.process_input(query)
            assert is_handled, f"Should handle: {query}"

    def test_notes_query(self, handler):
        """Test notes query."""
        is_handled, response = handler.process_input("mis notas")
        assert is_handled

    def test_non_reminder_query(self, handler):
        """Test non-reminder queries pass through."""
        is_handled, response = handler.process_input("qué hora es")
        assert not is_handled


class TestReminder:
    """Tests for Reminder dataclass."""

    def test_reminder_creation(self):
        """Test creating a reminder."""
        from modules.reminders import Reminder

        reminder = Reminder(
            id=1,
            message="Test",
            trigger_time=datetime.now()
        )

        assert reminder.id == 1
        assert reminder.message == "Test"
        assert not reminder.triggered

    def test_reminder_to_dict(self):
        """Test converting reminder to dict."""
        from modules.reminders import Reminder

        reminder = Reminder(
            id=1,
            message="Test",
            trigger_time=datetime.now()
        )

        d = reminder.to_dict()
        assert "id" in d
        assert "message" in d
        assert "trigger_time" in d
