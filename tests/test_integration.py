"""
Integration tests for JARVIS.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch
import yaml


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_config_file_exists(self, config_path):
        """Test that config file exists."""
        assert config_path.exists()

    def test_config_file_valid_yaml(self, config_path):
        """Test that config file is valid YAML."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert isinstance(config, dict)

    def test_config_has_required_sections(self, config_path):
        """Test that config has all required sections."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        required_sections = ['audio', 'wake_word', 'stt', 'tts', 'claude', 'behavior']
        for section in required_sections:
            assert section in config, f"Missing config section: {section}"

    def test_config_audio_settings(self, config_path):
        """Test audio configuration settings."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        audio = config['audio']
        assert audio['sample_rate'] == 16000
        assert audio['channels'] == 1

    def test_config_wake_word_settings(self, config_path):
        """Test wake word configuration settings."""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        ww = config['wake_word']
        assert 'model' in ww
        assert 'threshold' in ww
        assert 0.0 <= ww['threshold'] <= 1.0


class TestModelsAvailability:
    """Tests for model availability."""

    def test_vosk_model_exists(self, models_dir):
        """Test that Vosk model is downloaded."""
        model_path = models_dir / "vosk-model-small-es-0.42"

        if not model_path.exists():
            pytest.skip("Vosk model not downloaded")

        assert model_path.is_dir()
        # Check for essential files
        assert (model_path / "am").exists() or (model_path / "final.mdl").exists()

    def test_piper_model_exists(self, models_dir):
        """Test that Piper model is downloaded."""
        model_path = models_dir / "es_ES-davefx-medium.onnx"
        config_path = models_dir / "es_ES-davefx-medium.onnx.json"

        if not model_path.exists():
            pytest.skip("Piper model not downloaded")

        assert model_path.exists()
        assert config_path.exists()


class TestJarvisOrchestrator:
    """Tests for main Jarvis orchestrator."""

    def test_jarvis_init_with_missing_config(self, tmp_path):
        """Test Jarvis initialization with missing config file."""
        from jarvis import Jarvis

        # Should use default config
        with patch('modules.wake_word.WakeWordDetector'):
            with patch('modules.stt.SpeechToText'):
                with patch('modules.tts.TextToSpeech'):
                    with patch('modules.cli_bridge.ClaudeBridge'):
                        jarvis = Jarvis(config_path=str(tmp_path / "nonexistent.yaml"))
                        assert jarvis.config is not None

    def test_jarvis_shutdown(self, project_root):
        """Test Jarvis shutdown procedure."""
        from jarvis import Jarvis

        with patch('modules.wake_word.WakeWordDetector') as mock_ww:
            with patch('modules.stt.SpeechToText') as mock_stt:
                with patch('modules.tts.TextToSpeech') as mock_tts:
                    with patch('modules.cli_bridge.ClaudeBridge'):
                        jarvis = Jarvis(config_path=str(project_root / "config.yaml"))

                        # Mock module stop methods
                        mock_ww_instance = mock_ww.return_value
                        mock_stt_instance = mock_stt.return_value
                        mock_tts_instance = mock_tts.return_value

                        jarvis.shutdown()

                        assert jarvis.running is False
                        assert jarvis._shutdown_requested is True

    def test_default_config_structure(self, project_root):
        """Test that default config has correct structure."""
        from jarvis import Jarvis

        with patch('modules.wake_word.WakeWordDetector'):
            with patch('modules.stt.SpeechToText'):
                with patch('modules.tts.TextToSpeech'):
                    with patch('modules.cli_bridge.ClaudeBridge'):
                        jarvis = Jarvis(config_path="/nonexistent/path")
                        config = jarvis._default_config()

                        assert 'audio' in config
                        assert 'wake_word' in config
                        assert 'stt' in config
                        assert 'tts' in config
                        assert 'claude' in config
                        assert 'behavior' in config


class TestEndToEndFlow:
    """End-to-end flow tests (mocked)."""

    def test_conversation_flow(self, project_root):
        """Test a complete conversation flow with mocked components."""
        from jarvis import Jarvis

        with patch('jarvis.WakeWordDetector') as mock_ww:
            with patch('jarvis.SpeechToText') as mock_stt:
                with patch('jarvis.TextToSpeech') as mock_tts:
                    with patch('jarvis.ClaudeBridge') as mock_claude:
                        # Setup mocks
                        mock_ww_instance = mock_ww.return_value
                        mock_ww_instance.listen_once.return_value = True
                        mock_ww_instance.stop = MagicMock()

                        mock_stt_instance = mock_stt.return_value
                        mock_stt_instance.listen.return_value = "Hola Jarvis"

                        mock_tts_instance = mock_tts.return_value
                        mock_tts_instance.speak.return_value = True
                        mock_tts_instance.is_speaking = False
                        mock_tts_instance.wait = MagicMock()

                        mock_claude_instance = mock_claude.return_value
                        mock_claude_instance.send_with_context.return_value = "Hola, en qué puedo ayudarte?"

                        # Create Jarvis
                        jarvis = Jarvis(config_path=str(project_root / "config.yaml"))

                        # Simulate one interaction
                        jarvis._handle_interaction()

                        # Verify flow
                        mock_tts_instance.speak.assert_called()
                        mock_stt_instance.listen.assert_called()
                        mock_claude_instance.send_with_context.assert_called()

    def test_shutdown_command_detection(self, project_root):
        """Test that shutdown command is detected."""
        from jarvis import Jarvis

        with patch('jarvis.WakeWordDetector') as mock_ww:
            with patch('jarvis.SpeechToText') as mock_stt:
                with patch('jarvis.TextToSpeech') as mock_tts:
                    with patch('jarvis.ClaudeBridge'):
                        mock_ww_instance = mock_ww.return_value
                        mock_ww_instance.stop = MagicMock()

                        mock_stt_instance = mock_stt.return_value
                        mock_stt_instance.listen.return_value = "apágate"

                        mock_tts_instance = mock_tts.return_value
                        mock_tts_instance.speak.return_value = True
                        mock_tts_instance.is_speaking = False
                        mock_tts_instance.wait = MagicMock()

                        jarvis = Jarvis(config_path=str(project_root / "config.yaml"))
                        jarvis._handle_interaction()

                        assert jarvis._shutdown_requested is True
                        assert jarvis.running is False
