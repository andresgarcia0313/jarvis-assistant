"""
Tests for JARVIS Personality module.
"""

import pytest
from datetime import datetime
from unittest.mock import patch


class TestJarvisPersonality:
    """Tests for JarvisPersonality class."""

    def test_initialization_default(self):
        """Test default initialization."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        assert personality.user_name is None
        assert personality.formality_level == "formal"
        assert personality.conversation_count == 0

    def test_initialization_with_user_name(self):
        """Test initialization with user name."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality(user_name="Tony")

        assert personality.user_name == "Tony"

    def test_set_user_name(self):
        """Test setting user name."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        personality.set_user_name("Stark")

        assert personality.user_name == "Stark"

    def test_increment_conversation(self):
        """Test conversation counter."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        assert personality.conversation_count == 0

        personality.increment_conversation()
        assert personality.conversation_count == 1

        personality.increment_conversation()
        assert personality.conversation_count == 2


class TestGreetings:
    """Tests for greeting functionality."""

    def test_morning_greeting(self):
        """Test morning greeting (5-11)."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 9
            greeting = personality.get_greeting()

        assert "Buenos días" in greeting

    def test_afternoon_greeting(self):
        """Test afternoon greeting (12-18)."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 15
            greeting = personality.get_greeting()

        assert "Buenas tardes" in greeting

    def test_evening_greeting(self):
        """Test evening greeting (19-4)."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 21
            greeting = personality.get_greeting()

        assert "Buenas noches" in greeting

    def test_greeting_with_user_name(self):
        """Test greeting includes user name."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality(user_name="Tony")

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 10
            greeting = personality.get_greeting()

        assert "Tony" in greeting


class TestWakeResponses:
    """Tests for wake word response functionality."""

    def test_wake_response_not_empty(self):
        """Test wake response is not empty."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        response = personality.get_wake_response()

        assert response
        assert len(response) > 0

    def test_wake_response_variations(self):
        """Test that wake responses have variations."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        responses = set()

        for _ in range(20):
            responses.add(personality.get_wake_response())

        # Should have at least 2 different responses
        assert len(responses) >= 2


class TestPhrases:
    """Tests for various phrase types."""

    def test_confirmation_phrases(self):
        """Test confirmation phrases."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        confirmation = personality.get_confirmation()

        assert confirmation
        assert confirmation in [
            "Entendido.",
            "Muy bien.",
            "Ciertamente.",
            "Por supuesto.",
            "De acuerdo.",
        ]

    def test_processing_messages(self):
        """Test processing messages."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        processing = personality.get_processing_message()

        assert processing
        assert "..." in processing

    def test_limitation_messages(self):
        """Test limitation messages."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        limitation = personality.get_limitation_message()

        assert limitation
        assert "temo" in limitation or "Lamentablemente" in limitation or "confesar" in limitation

    def test_farewell_messages(self):
        """Test farewell messages."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        farewell = personality.get_farewell()

        assert farewell
        assert any(word in farewell for word in ["pronto", "día", "servicio", "luego"])


class TestSystemPrompt:
    """Tests for system prompt generation."""

    def test_system_prompt_not_empty(self):
        """Test system prompt is generated."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        prompt = personality.get_system_prompt()

        assert prompt
        assert len(prompt) > 100

    def test_system_prompt_contains_jarvis_identity(self):
        """Test system prompt contains JARVIS identity."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        prompt = personality.get_system_prompt()

        assert "JARVIS" in prompt

    def test_system_prompt_contains_personality_traits(self):
        """Test system prompt contains personality traits."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        prompt = personality.get_system_prompt()

        assert "señor" in prompt.lower()
        assert "británico" in prompt.lower() or "elegante" in prompt.lower()

    def test_system_prompt_includes_user_name(self):
        """Test system prompt includes user name when set."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality(user_name="Tony")
        prompt = personality.get_system_prompt()

        assert "Tony" in prompt

    def test_system_prompt_includes_time_context(self):
        """Test system prompt includes time context."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 10
            prompt = personality.get_system_prompt()

        assert "mañana" in prompt.lower()


class TestStartupShutdown:
    """Tests for startup and shutdown messages."""

    def test_startup_message_morning(self):
        """Test startup message in morning."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 9
            message = personality.get_startup_message()

        assert "JARVIS" in message
        assert "Buenos días" in message

    def test_startup_message_afternoon(self):
        """Test startup message in afternoon."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()

        with patch('modules.personality.datetime') as mock_dt:
            mock_dt.now.return_value.hour = 15
            message = personality.get_startup_message()

        assert "JARVIS" in message
        assert "Buenas tardes" in message

    def test_shutdown_message(self):
        """Test shutdown message."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        message = personality.get_shutdown_message()

        assert message
        assert "Desactivando" in message or any(
            word in message for word in ["pronto", "día", "servicio", "luego"]
        )


class TestEnhanceResponse:
    """Tests for response enhancement."""

    def test_enhance_response_passthrough(self):
        """Test that enhance_response passes through by default."""
        from modules.personality import JarvisPersonality

        personality = JarvisPersonality()
        original = "This is a test response."
        enhanced = personality.enhance_response(original)

        assert enhanced == original


class TestGetPersonalitySingleton:
    """Tests for singleton pattern."""

    def test_get_personality_creates_instance(self):
        """Test that get_personality creates an instance."""
        from modules import personality as p

        # Reset singleton
        p._personality_instance = None

        instance = p.get_personality()

        assert instance is not None
        assert isinstance(instance, p.JarvisPersonality)

    def test_get_personality_returns_same_instance(self):
        """Test that get_personality returns the same instance."""
        from modules import personality as p

        # Reset singleton
        p._personality_instance = None

        instance1 = p.get_personality()
        instance2 = p.get_personality()

        assert instance1 is instance2

    def test_get_personality_updates_user_name(self):
        """Test that get_personality updates user name."""
        from modules import personality as p

        # Reset singleton
        p._personality_instance = None

        instance = p.get_personality(user_name="Tony")
        assert instance.user_name == "Tony"

        p.get_personality(user_name="Pepper")
        assert instance.user_name == "Pepper"
