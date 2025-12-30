"""
Tests for Speech-to-Text module.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import numpy as np


class TestSpeechToText:
    """Tests for SpeechToText class."""

    def test_model_path_validation(self, project_root):
        """Test that invalid model path raises FileNotFoundError."""
        from modules.stt import SpeechToText

        with pytest.raises(FileNotFoundError):
            SpeechToText(model_path="/nonexistent/path")

    def test_model_loads_successfully(self, models_dir):
        """Test that Vosk model loads correctly."""
        from modules.stt import SpeechToText

        model_path = models_dir / "vosk-model-small-es-0.42"
        if not model_path.exists():
            pytest.skip("Vosk model not downloaded")

        stt = SpeechToText(model_path=str(model_path))
        assert stt.model is not None
        assert stt.recognizer is not None
        assert stt.sample_rate == 16000

    def test_stop_listening(self, models_dir):
        """Test that stop() sets flags correctly."""
        from modules.stt import SpeechToText

        model_path = models_dir / "vosk-model-small-es-0.42"
        if not model_path.exists():
            pytest.skip("Vosk model not downloaded")

        stt = SpeechToText(model_path=str(model_path))
        stt.is_listening = True
        stt.stop()

        assert stt._stop_requested is True
        assert stt.is_listening is False

    def test_listen_returns_none_on_empty_input(self, models_dir):
        """Test listen returns None when no speech detected."""
        from modules.stt import SpeechToText

        model_path = models_dir / "vosk-model-small-es-0.42"
        if not model_path.exists():
            pytest.skip("Vosk model not downloaded")

        stt = SpeechToText(
            model_path=str(model_path),
            silence_timeout=0.1,
            max_recording_time=0.5
        )

        # Mock audio stream to return silence
        with patch('sounddevice.RawInputStream') as mock_stream:
            mock_context = MagicMock()
            mock_stream.return_value.__enter__ = MagicMock(return_value=mock_context)
            mock_stream.return_value.__exit__ = MagicMock(return_value=False)

            # Simulate immediate stop
            stt._stop_requested = True
            result = stt.listen()

            assert result is None

    def test_configuration_parameters(self, models_dir):
        """Test that configuration parameters are set correctly."""
        from modules.stt import SpeechToText

        model_path = models_dir / "vosk-model-small-es-0.42"
        if not model_path.exists():
            pytest.skip("Vosk model not downloaded")

        stt = SpeechToText(
            model_path=str(model_path),
            sample_rate=8000,
            silence_timeout=3.0,
            max_recording_time=60.0
        )

        assert stt.sample_rate == 8000
        assert stt.silence_timeout == 3.0
        assert stt.max_recording_time == 60.0


class TestDownloadModel:
    """Tests for model download functionality."""

    def test_download_model_creates_directory(self, tmp_path):
        """Test that download_model creates target directory."""
        from modules.stt import download_model

        target_dir = tmp_path / "models"
        # Don't actually download, just verify directory creation logic
        assert not target_dir.exists()

        # The function should handle non-existent directories
        with patch('urllib.request.urlretrieve') as mock_download:
            with patch('zipfile.ZipFile'):
                try:
                    download_model("test-model", str(target_dir))
                except:
                    pass  # Expected to fail without network

        # Directory should be created
        assert target_dir.exists()
