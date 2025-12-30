"""
Tests for Text-to-Speech module.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np


class TestTextToSpeech:
    """Tests for TextToSpeech class."""

    def test_model_path_validation(self):
        """Test that invalid model path raises FileNotFoundError when Piper available."""
        from modules.tts import TextToSpeech, PIPER_AVAILABLE

        if not PIPER_AVAILABLE:
            pytest.skip("Piper not available")

        with pytest.raises(FileNotFoundError):
            TextToSpeech(model_path="/nonexistent/path")

    def test_fallback_to_espeak_when_piper_unavailable(self):
        """Test that espeak fallback is used when Piper not available."""
        from modules import tts

        # Temporarily disable Piper
        original_available = tts.PIPER_AVAILABLE
        tts.PIPER_AVAILABLE = False

        try:
            tts_instance = tts.TextToSpeech(model_path="/any/path")
            assert tts_instance.voice is None
            assert tts_instance.sample_rate == 22050
        finally:
            tts.PIPER_AVAILABLE = original_available

    def test_model_loads_successfully(self, models_dir):
        """Test that Piper model loads correctly."""
        from modules.tts import TextToSpeech, PIPER_AVAILABLE

        if not PIPER_AVAILABLE:
            pytest.skip("Piper not available")

        model_path = models_dir / "es_ES-davefx-medium.onnx"
        if not model_path.exists():
            pytest.skip("Piper model not downloaded")

        tts = TextToSpeech(model_path=str(model_path))
        assert tts.voice is not None

    def test_stop_sets_flags(self, models_dir):
        """Test that stop() sets flags correctly."""
        from modules.tts import TextToSpeech, PIPER_AVAILABLE

        if not PIPER_AVAILABLE:
            pytest.skip("Piper not available")

        model_path = models_dir / "es_ES-davefx-medium.onnx"
        if not model_path.exists():
            pytest.skip("Piper model not downloaded")

        tts = TextToSpeech(model_path=str(model_path))
        tts.stop()

        assert tts._stop_requested is True

    def test_speak_empty_text_returns_true(self, models_dir):
        """Test that speaking empty text returns True immediately."""
        from modules.tts import TextToSpeech, PIPER_AVAILABLE

        if not PIPER_AVAILABLE:
            pytest.skip("Piper not available")

        model_path = models_dir / "es_ES-davefx-medium.onnx"
        if not model_path.exists():
            pytest.skip("Piper model not downloaded")

        tts = TextToSpeech(model_path=str(model_path))
        result = tts.speak("")

        assert result is True

    def test_speak_with_interruption(self, models_dir):
        """Test that speech can be interrupted."""
        from modules.tts import TextToSpeech, PIPER_AVAILABLE

        if not PIPER_AVAILABLE:
            pytest.skip("Piper not available")

        model_path = models_dir / "es_ES-davefx-medium.onnx"
        if not model_path.exists():
            pytest.skip("Piper model not downloaded")

        tts = TextToSpeech(model_path=str(model_path))

        # Pre-set stop flag
        tts._stop_requested = True
        result = tts._speak_blocking("Test text")

        assert result is False

    def test_espeak_fallback(self):
        """Test espeak fallback method."""
        from modules import tts

        original_available = tts.PIPER_AVAILABLE
        tts.PIPER_AVAILABLE = False

        try:
            tts_instance = tts.TextToSpeech(model_path="/any/path")

            with patch('subprocess.Popen') as mock_popen:
                mock_process = MagicMock()
                mock_process.poll.return_value = 0
                mock_process.returncode = 0
                mock_popen.return_value = mock_process

                result = tts_instance._speak_espeak("Hola")
                assert result is True
                mock_popen.assert_called_once()
        finally:
            tts.PIPER_AVAILABLE = original_available

    def test_configuration_parameters(self, models_dir):
        """Test that configuration parameters are set correctly."""
        from modules.tts import TextToSpeech, PIPER_AVAILABLE

        if not PIPER_AVAILABLE:
            pytest.skip("Piper not available")

        model_path = models_dir / "es_ES-davefx-medium.onnx"
        if not model_path.exists():
            pytest.skip("Piper model not downloaded")

        tts = TextToSpeech(
            model_path=str(model_path),
            speed=1.5,
            speaker_id=1
        )

        assert tts.speed == 1.5
        assert tts.speaker_id == 1
