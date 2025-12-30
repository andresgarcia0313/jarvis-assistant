"""
Tests for JARVIS Sounds and UI modules.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestSoundEvent:
    """Tests for SoundEvent enum."""

    def test_sound_events(self):
        """Test SoundEvent enum values."""
        from sounds import SoundEvent

        assert SoundEvent.STARTUP.value == "startup"
        assert SoundEvent.LISTENING.value == "listening"
        assert SoundEvent.COMPLETE.value == "complete"
        assert SoundEvent.ERROR.value == "error"


class TestSoundManager:
    """Tests for SoundManager class."""

    @pytest.fixture
    def sound_manager(self):
        """Create a SoundManager instance."""
        from sounds import SoundManager

        with patch('shutil.which', return_value="/usr/bin/paplay"):
            manager = SoundManager(enabled=True)
            yield manager

    def test_initialization(self, sound_manager):
        """Test SoundManager initialization."""
        assert sound_manager.enabled
        assert sound_manager.player is not None

    def test_set_enabled(self, sound_manager):
        """Test enabling/disabling sounds."""
        sound_manager.set_enabled(False)
        assert not sound_manager.enabled

        sound_manager.set_enabled(True)
        assert sound_manager.enabled

    def test_set_volume(self, sound_manager):
        """Test setting volume."""
        sound_manager.set_volume(0.8)
        assert sound_manager._volume == 0.8

        # Test clamping
        sound_manager.set_volume(1.5)
        assert sound_manager._volume == 1.0

        sound_manager.set_volume(-0.5)
        assert sound_manager._volume == 0.0

    def test_play_disabled(self, sound_manager):
        """Test that play does nothing when disabled."""
        from sounds import SoundEvent

        sound_manager.set_enabled(False)

        with patch.object(sound_manager, '_play_file') as mock_play:
            with patch.object(sound_manager, '_play_tones') as mock_tones:
                sound_manager.play(SoundEvent.STARTUP)

                mock_play.assert_not_called()
                mock_tones.assert_not_called()

    def test_play_file_not_found(self, sound_manager):
        """Test playing when WAV file not found."""
        from sounds import SoundEvent

        with patch.object(sound_manager, '_play_tones') as mock_tones:
            sound_manager.play(SoundEvent.STARTUP)
            # Should fall back to tones
            mock_tones.assert_called_once()

    def test_convenience_methods(self, sound_manager):
        """Test convenience play methods."""
        with patch.object(sound_manager, 'play') as mock_play:
            from sounds import SoundEvent

            sound_manager.play_startup()
            mock_play.assert_called_with(SoundEvent.STARTUP)

            sound_manager.play_listening()
            mock_play.assert_called_with(SoundEvent.LISTENING)

            sound_manager.play_complete()
            mock_play.assert_called_with(SoundEvent.COMPLETE)

            sound_manager.play_error()
            mock_play.assert_called_with(SoundEvent.ERROR)

    def test_no_player_available(self):
        """Test when no audio player is available."""
        from sounds import SoundManager

        with patch('shutil.which', return_value=None):
            manager = SoundManager()
            assert manager.player is None


class TestJarvisState:
    """Tests for JarvisState enum."""

    def test_state_values(self):
        """Test JarvisState enum values."""
        from ui import JarvisState

        assert JarvisState.IDLE.value == "idle"
        assert JarvisState.LISTENING.value == "listening"
        assert JarvisState.PROCESSING.value == "processing"
        assert JarvisState.SPEAKING.value == "speaking"
        assert JarvisState.ERROR.value == "error"


class TestWidgetController:
    """Tests for WidgetController class."""

    @pytest.fixture
    def controller(self):
        """Create a WidgetController instance."""
        from ui import WidgetController

        return WidgetController()

    def test_initialization(self, controller):
        """Test WidgetController initialization."""
        from ui import JarvisState

        assert controller.state == JarvisState.IDLE
        assert controller.message == ""
        assert controller.command_history == []

    def test_set_state(self, controller):
        """Test setting state."""
        from ui import JarvisState

        controller.set_state(JarvisState.LISTENING, "Esperando...")

        assert controller.state == JarvisState.LISTENING
        assert controller.message == "Esperando..."

    def test_add_command(self, controller):
        """Test adding commands to history."""
        controller.add_command("primer comando")
        controller.add_command("segundo comando")

        assert len(controller.command_history) == 2
        assert controller.command_history[0] == "segundo comando"

    def test_command_history_limit(self, controller):
        """Test command history respects max limit."""
        for i in range(10):
            controller.add_command(f"comando {i}")

        assert len(controller.command_history) == controller.max_history

    def test_callback_notification(self, controller):
        """Test that callbacks are notified."""
        from ui import JarvisState

        callback_called = []

        def callback(state, message):
            callback_called.append((state, message))

        controller.add_callback(callback)
        controller.set_state(JarvisState.PROCESSING, "test")

        assert len(callback_called) == 1
        assert callback_called[0] == (JarvisState.PROCESSING, "test")

    def test_get_state_text(self, controller):
        """Test getting human-readable state text."""
        from ui import JarvisState

        controller.set_state(JarvisState.LISTENING)
        text = controller.get_state_text()

        assert "Escuchando" in text

    def test_get_status_summary(self, controller):
        """Test getting status summary."""
        from ui import JarvisState

        controller.set_state(JarvisState.IDLE, "En espera")
        controller.add_command("hola jarvis")

        summary = controller.get_status_summary()

        assert "Estado" in summary
        assert "hola jarvis" in summary


class TestWidgetManager:
    """Tests for WidgetManager class."""

    @pytest.fixture
    def manager(self):
        """Create a WidgetManager instance."""
        from ui import WidgetManager

        # Disable Qt to avoid GUI issues in tests
        return WidgetManager(enabled=False)

    def test_initialization(self, manager):
        """Test WidgetManager initialization."""
        assert not manager.enabled
        assert manager.controller is not None

    def test_set_state(self, manager):
        """Test setting state through manager."""
        from ui import JarvisState

        manager.set_state(JarvisState.LISTENING, "test")

        assert manager.controller.state == JarvisState.LISTENING

    def test_add_command(self, manager):
        """Test adding command through manager."""
        manager.add_command("test command")

        assert "test command" in manager.controller.command_history


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_sound_manager(self):
        """Test get_sound_manager returns instance."""
        from sounds import get_sound_manager
        import sounds

        # Reset singleton
        sounds._sound_manager = None

        with patch('shutil.which', return_value="/usr/bin/paplay"):
            manager = get_sound_manager()
            assert manager is not None

    def test_get_widget_controller(self):
        """Test get_widget_controller returns instance."""
        from ui import get_widget_controller
        import ui

        # Reset singleton
        ui._widget_controller = None

        controller = get_widget_controller()
        assert controller is not None

    def test_get_widget_manager(self):
        """Test get_widget_manager returns instance."""
        from ui import get_widget_manager
        import ui

        # Reset singleton
        ui._widget_manager = None

        manager = get_widget_manager(enabled=False)
        assert manager is not None
