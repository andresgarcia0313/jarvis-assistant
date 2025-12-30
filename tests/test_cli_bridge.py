"""
Tests for Claude CLI Bridge module.
"""

import pytest
from unittest.mock import MagicMock, patch
import subprocess


class TestClaudeBridge:
    """Tests for ClaudeBridge class."""

    def test_claude_cli_not_found(self):
        """Test that missing Claude CLI raises RuntimeError."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value=None):
            with pytest.raises(RuntimeError) as exc_info:
                ClaudeBridge(command="nonexistent_command")

            assert "not found" in str(exc_info.value).lower()

    def test_claude_cli_found(self):
        """Test that existing Claude CLI initializes correctly."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()
            assert bridge.command == "claude"
            assert bridge.timeout == 60

    def test_send_empty_message(self):
        """Test that empty message returns None."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()
            result = bridge.send("")

            assert result is None

    def test_send_message_success(self):
        """Test successful message sending."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Hello, I'm Claude!",
                    stderr=""
                )

                result = bridge.send("Hello")

                assert result == "Hello, I'm Claude!"
                mock_run.assert_called_once()

    def test_send_message_error(self):
        """Test error handling when Claude CLI fails."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=1,
                    stdout="",
                    stderr="Error occurred"
                )

                result = bridge.send("Hello")

                assert result is None

    def test_send_message_timeout(self):
        """Test timeout handling."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge(timeout=1)

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = subprocess.TimeoutExpired(
                    cmd="claude",
                    timeout=1
                )

                result = bridge.send("Hello")

                assert result is None

    def test_send_with_context(self):
        """Test sending message with context."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(
                    returncode=0,
                    stdout="Response",
                    stderr=""
                )

                result = bridge.send_with_context(
                    "New question",
                    context="Previous conversation"
                )

                assert result == "Response"
                # Check that context was included
                call_args = mock_run.call_args
                assert "Previous conversation" in call_args[0][0][2]

    def test_check_connection_success(self):
        """Test connection check when CLI works."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()

            with patch('subprocess.run') as mock_run:
                mock_run.return_value = MagicMock(returncode=0)

                result = bridge.check_connection()

                assert result is True

    def test_check_connection_failure(self):
        """Test connection check when CLI fails."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/claude"):
            bridge = ClaudeBridge()

            with patch('subprocess.run') as mock_run:
                mock_run.side_effect = Exception("Connection failed")

                result = bridge.check_connection()

                assert result is False

    def test_configuration_parameters(self):
        """Test that configuration parameters are set correctly."""
        from modules.cli_bridge import ClaudeBridge

        with patch('shutil.which', return_value="/usr/bin/custom-claude"):
            bridge = ClaudeBridge(
                command="custom-claude",
                timeout=120,
                system_prompt="You are JARVIS"
            )

            assert bridge.command == "custom-claude"
            assert bridge.timeout == 120
            assert bridge.system_prompt == "You are JARVIS"


class TestConversationManager:
    """Tests for ConversationManager class."""

    def test_add_exchange(self):
        """Test adding conversation exchanges."""
        from modules.cli_bridge import ConversationManager

        manager = ConversationManager()
        manager.add_exchange("Hello", "Hi there!")

        assert len(manager.history) == 1
        assert manager.history[0]["user"] == "Hello"
        assert manager.history[0]["assistant"] == "Hi there!"

    def test_max_history_limit(self):
        """Test that history is limited to max_history."""
        from modules.cli_bridge import ConversationManager

        manager = ConversationManager(max_history=3)

        for i in range(5):
            manager.add_exchange(f"Question {i}", f"Answer {i}")

        assert len(manager.history) == 3
        # Should have last 3 exchanges
        assert manager.history[0]["user"] == "Question 2"
        assert manager.history[2]["user"] == "Question 4"

    def test_get_context(self):
        """Test context string generation."""
        from modules.cli_bridge import ConversationManager

        manager = ConversationManager()
        manager.add_exchange("Hello", "Hi!")
        manager.add_exchange("How are you?", "I'm good!")

        context = manager.get_context()

        assert "Usuario: Hello" in context
        assert "JARVIS: Hi!" in context
        assert "Usuario: How are you?" in context
        assert "JARVIS: I'm good!" in context

    def test_get_context_empty(self):
        """Test context string when history is empty."""
        from modules.cli_bridge import ConversationManager

        manager = ConversationManager()
        context = manager.get_context()

        assert context == ""

    def test_clear_history(self):
        """Test clearing conversation history."""
        from modules.cli_bridge import ConversationManager

        manager = ConversationManager()
        manager.add_exchange("Hello", "Hi!")
        manager.clear()

        assert len(manager.history) == 0
