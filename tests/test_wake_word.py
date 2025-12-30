"""
Tests for Wake Word Detection module.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np


class TestWakeWordDetector:
    """Tests for WakeWordDetector class."""

    def test_openwakeword_not_available(self):
        """Test behavior when OpenWakeWord is not available."""
        from modules import wake_word

        original_available = wake_word.OPENWAKEWORD_AVAILABLE
        wake_word.OPENWAKEWORD_AVAILABLE = False

        try:
            with pytest.raises(RuntimeError):
                wake_word.WakeWordDetector()
        finally:
            wake_word.OPENWAKEWORD_AVAILABLE = original_available

    def test_model_loads_successfully(self):
        """Test that wake word model loads correctly."""
        from modules.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE

        if not OPENWAKEWORD_AVAILABLE:
            pytest.skip("OpenWakeWord not available")

        detector = WakeWordDetector(model_name="hey_jarvis_v0.1")
        assert detector.model is not None
        assert detector.threshold == 0.5

    def test_fallback_model_used(self):
        """Test that fallback model is used when primary not found."""
        from modules.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE

        if not OPENWAKEWORD_AVAILABLE:
            pytest.skip("OpenWakeWord not available")

        # Use a non-existent model name to trigger fallback
        detector = WakeWordDetector(
            model_name="nonexistent_model_xyz",
            fallback_model="alexa_v0.1"
        )

        # Should have loaded fallback model
        assert detector.model is not None
        assert detector.model_name == "alexa_v0.1"

    def test_stop_sets_flags(self):
        """Test that stop() sets flags correctly."""
        from modules.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE

        if not OPENWAKEWORD_AVAILABLE:
            pytest.skip("OpenWakeWord not available")

        detector = WakeWordDetector()
        detector.is_listening = True
        detector.stop()

        assert detector._stop_requested is True
        assert detector.is_listening is False

    def test_configuration_parameters(self):
        """Test that configuration parameters are set correctly."""
        from modules.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE

        if not OPENWAKEWORD_AVAILABLE:
            pytest.skip("OpenWakeWord not available")

        detector = WakeWordDetector(
            threshold=0.7,
            sample_rate=8000
        )

        assert detector.threshold == 0.7
        assert detector.sample_rate == 8000

    def test_listen_once_with_timeout(self):
        """Test listen_once returns False on timeout."""
        from modules.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE

        if not OPENWAKEWORD_AVAILABLE:
            pytest.skip("OpenWakeWord not available")

        detector = WakeWordDetector()

        # Mock audio stream
        with patch('sounddevice.InputStream') as mock_stream:
            mock_context = MagicMock()
            mock_stream.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_stream.return_value.__exit__ = MagicMock(return_value=False)

            # Very short timeout should return False
            result = detector.listen_once(timeout=0.1)

            # Should return False (timeout, no detection)
            assert result is False

    def test_audio_callback_processes_data(self):
        """Test that audio callback processes data correctly."""
        from modules.wake_word import WakeWordDetector, OPENWAKEWORD_AVAILABLE

        if not OPENWAKEWORD_AVAILABLE:
            pytest.skip("OpenWakeWord not available")

        detector = WakeWordDetector()

        # Create mock audio data
        mock_audio = np.zeros((1280, 1), dtype=np.float32)

        # Call callback
        detector._audio_callback(mock_audio, 1280, None, None)

        # Check that data was added to queue
        assert not detector.audio_queue.empty()


class TestCreateJarvisModel:
    """Tests for custom model creation instructions."""

    def test_create_jarvis_model_logs_info(self, caplog):
        """Test that create_jarvis_model logs appropriate info."""
        from modules.wake_word import create_jarvis_model
        import logging

        with caplog.at_level(logging.INFO):
            create_jarvis_model()

        # Should have logged info about custom model
        assert len(caplog.records) > 0
