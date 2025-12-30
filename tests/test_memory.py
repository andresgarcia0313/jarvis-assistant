"""
Tests for JARVIS Memory module.
"""

import pytest
import tempfile
import os
from pathlib import Path


class TestMemoryDatabase:
    """Tests for MemoryDatabase class."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        from memory.database import MemoryDatabase
        db = MemoryDatabase(db_path)

        yield db

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_initialization_creates_db(self, temp_db):
        """Test database file is created."""
        assert temp_db.db_path.exists()

    def test_set_and_get_preference(self, temp_db):
        """Test setting and getting preferences."""
        temp_db.set_preference("theme", "dark")
        assert temp_db.get_preference("theme") == "dark"

    def test_get_preference_default(self, temp_db):
        """Test getting non-existent preference returns default."""
        assert temp_db.get_preference("nonexistent", "default") == "default"

    def test_preference_json_values(self, temp_db):
        """Test preferences can store JSON values."""
        temp_db.set_preference("settings", {"volume": 80, "muted": False})
        result = temp_db.get_preference("settings")
        assert result == {"volume": 80, "muted": False}

    def test_get_all_preferences(self, temp_db):
        """Test getting all preferences."""
        temp_db.set_preference("key1", "value1")
        temp_db.set_preference("key2", "value2")
        prefs = temp_db.get_all_preferences()
        assert "key1" in prefs
        assert "key2" in prefs

    def test_delete_preference(self, temp_db):
        """Test deleting a preference."""
        temp_db.set_preference("to_delete", "value")
        assert temp_db.delete_preference("to_delete")
        assert temp_db.get_preference("to_delete") is None

    def test_add_memory(self, temp_db):
        """Test adding a memory."""
        memory_id = temp_db.add_memory(
            "Mi cliente principal es RSM",
            category="trabajo",
            keywords=["cliente", "RSM"]
        )
        assert memory_id > 0

    def test_search_memories(self, temp_db):
        """Test searching memories."""
        temp_db.add_memory("El cumpleaños de María es el 15 de mayo")
        temp_db.add_memory("Mi proyecto actual es JARVIS")

        results = temp_db.search_memories("María")
        assert len(results) == 1
        assert "María" in results[0]["content"]

    def test_search_memories_by_category(self, temp_db):
        """Test searching memories by category."""
        temp_db.add_memory("Info personal", category="personal")
        temp_db.add_memory("Info trabajo", category="trabajo")

        results = temp_db.search_memories(category="trabajo")
        assert len(results) == 1
        assert results[0]["category"] == "trabajo"

    def test_forget_about(self, temp_db):
        """Test forgetting memories about a topic."""
        temp_db.add_memory("RSM es mi cliente")
        temp_db.add_memory("RSM tiene oficinas en Colombia")
        temp_db.add_memory("Otro tema diferente")

        count = temp_db.forget_about("RSM")
        assert count == 2

        results = temp_db.search_memories("RSM")
        assert len(results) == 0

    def test_session_management(self, temp_db):
        """Test session creation and ending."""
        session_id = temp_db.start_session()
        assert session_id is not None

        temp_db.end_session(session_id)
        sessions = temp_db.get_recent_sessions()
        assert len(sessions) == 1
        assert sessions[0]["ended_at"] is not None

    def test_conversation_history(self, temp_db):
        """Test conversation history storage."""
        session_id = temp_db.start_session()

        temp_db.add_conversation(session_id, "user", "Hola JARVIS")
        temp_db.add_conversation(session_id, "assistant", "Buenos días, señor")

        history = temp_db.get_conversation_history(session_id)
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "assistant"

    def test_user_name_storage(self, temp_db):
        """Test user name storage and retrieval."""
        assert temp_db.get_user_name() is None

        temp_db.set_user_name("Tony")
        assert temp_db.get_user_name() == "Tony"

    def test_memory_summary(self, temp_db):
        """Test memory summary generation."""
        temp_db.add_memory("Test memory")
        temp_db.set_preference("pref", "value")
        temp_db.start_session()

        summary = temp_db.get_memory_summary()
        assert summary["memories"] == 1
        assert summary["preferences"] == 1
        assert summary["sessions"] == 1

    def test_export_memories(self, temp_db):
        """Test memory export."""
        temp_db.add_memory("Test memory")
        temp_db.set_preference("key", "value")

        export = temp_db.export_memories()
        assert "preferences" in export
        assert "memories" in export
        assert "exported_at" in export

    def test_clear_all(self, temp_db):
        """Test clearing all data."""
        temp_db.add_memory("Memory")
        temp_db.set_preference("key", "value")
        temp_db.start_session()

        temp_db.clear_all()

        summary = temp_db.get_memory_summary()
        assert summary["memories"] == 0
        assert summary["preferences"] == 0


class TestMemoryHandler:
    """Tests for MemoryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a memory handler with temp database."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        from memory.database import MemoryDatabase
        from memory.memory_handler import MemoryHandler

        db = MemoryDatabase(db_path)
        handler = MemoryHandler(db)

        yield handler

        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_remember_command(self, handler):
        """Test 'recuerda que' command."""
        is_cmd, response = handler.process_input("recuerda que mi cliente es RSM")
        assert is_cmd
        assert response is not None

        # Verify memory was stored
        memories = handler.db.search_memories("RSM")
        assert len(memories) == 1

    def test_remember_variations(self, handler):
        """Test different remember command variations."""
        commands = [
            "recuerda que tengo reunión mañana",
            "anota que debo llamar a Juan",
            "guarda que mi contraseña es segura",
            "no olvides que el proyecto termina en marzo",
        ]

        for cmd in commands:
            is_cmd, response = handler.process_input(cmd)
            assert is_cmd, f"Should recognize: {cmd}"
            assert response is not None

    def test_forget_command(self, handler):
        """Test 'olvida' command."""
        handler.process_input("recuerda que mi cliente es RSM")
        is_cmd, response = handler.process_input("olvida lo de RSM")

        assert is_cmd
        assert "olvidado" in response.lower() or "RSM" in response

    def test_recall_command(self, handler):
        """Test recall command."""
        handler.process_input("recuerda que María cumple el 15 de mayo")

        is_cmd, response = handler.process_input("qué recuerdas sobre María")
        assert is_cmd
        assert "María" in response or "15 de mayo" in response

    def test_recall_nothing(self, handler):
        """Test recall when no memories exist."""
        is_cmd, response = handler.process_input("qué sabes de algo inexistente")
        assert is_cmd
        assert "no tengo" in response.lower()

    def test_name_learning(self, handler):
        """Test learning user name."""
        is_cmd, response = handler.process_input("me llamo Tony")
        assert is_cmd
        assert "Tony" in response

        # Verify name was stored
        assert handler.db.get_user_name() == "Tony"

    def test_name_variations(self, handler):
        """Test different name introduction patterns."""
        patterns = [
            ("soy Andrés", "Andrés"),
            ("mi nombre es Carlos", "Carlos"),
            ("puedes llamarme Pedro", "Pedro"),
        ]

        for cmd, expected_name in patterns:
            # Reset
            handler.db.set_preference("user_name", None)

            is_cmd, response = handler.process_input(cmd)
            assert is_cmd, f"Should recognize: {cmd}"
            assert handler.db.get_user_name() == expected_name

    def test_non_memory_command(self, handler):
        """Test non-memory commands pass through."""
        is_cmd, response = handler.process_input("qué hora es")
        assert not is_cmd
        assert response is None

    def test_session_management(self, handler):
        """Test session start and end."""
        session_id = handler.start_session()
        assert session_id is not None
        assert handler.current_session_id == session_id

        handler.end_session()
        assert handler.current_session_id is None

    def test_conversation_history_tracking(self, handler):
        """Test conversation history is tracked."""
        handler.start_session()
        handler.add_to_history("user", "Hola")
        handler.add_to_history("assistant", "Buenos días")

        context = handler.get_conversation_context()
        assert "Hola" in context or len(context) > 0

    def test_context_for_prompt(self, handler):
        """Test memory context generation for prompts."""
        handler.db.set_user_name("Tony")
        handler.process_input("recuerda que trabajo en Stark Industries")

        context = handler.get_context_for_prompt()
        assert "Tony" in context
        assert "Stark" in context

    def test_category_detection(self, handler):
        """Test automatic category detection."""
        handler.process_input("recuerda que mi cliente principal es RSM")
        memories = handler.db.search_memories("RSM")
        assert memories[0]["category"] == "trabajo"

        handler.process_input("recuerda que me gusta el café")
        memories = handler.db.search_memories("café")
        assert memories[0]["category"] == "preferencias"


class TestMemorySingleton:
    """Tests for singleton pattern."""

    def test_get_memory_creates_instance(self):
        """Test that get_memory creates an instance."""
        from memory import database

        # Reset singleton
        database._memory_instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            instance = database.get_memory(db_path)
            assert instance is not None

    def test_get_memory_handler_creates_instance(self):
        """Test that get_memory_handler creates an instance."""
        from memory import memory_handler, database

        # Reset singletons
        memory_handler._handler_instance = None
        database._memory_instance = None

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            database._memory_instance = database.MemoryDatabase(db_path)

            handler = memory_handler.get_memory_handler()
            assert handler is not None


class TestMemoryPersistence:
    """Tests for memory persistence across instances."""

    def test_data_persists_across_instances(self):
        """Test that data persists when database is reopened."""
        from memory.database import MemoryDatabase

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # First instance - write data
            db1 = MemoryDatabase(db_path)
            db1.set_user_name("Persistent User")
            db1.add_memory("Persistent memory content")
            del db1

            # Second instance - read data
            db2 = MemoryDatabase(db_path)
            assert db2.get_user_name() == "Persistent User"
            memories = db2.search_memories("Persistent")
            assert len(memories) == 1
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_sessions_persist(self):
        """Test that session data persists."""
        from memory.database import MemoryDatabase

        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name

        try:
            # First instance
            db1 = MemoryDatabase(db_path)
            session_id = db1.start_session()
            db1.add_conversation(session_id, "user", "Test message")
            del db1

            # Second instance
            db2 = MemoryDatabase(db_path)
            sessions = db2.get_recent_sessions()
            assert len(sessions) == 1
            history = db2.get_conversation_history(session_id)
            assert len(history) == 1
            assert history[0]["content"] == "Test message"
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
