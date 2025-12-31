"""
Tests E2E para el módulo TTS con soporte Piper.
Prueba selección de modelos por calidad y descarga automática.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, '/home/andres/Desarrollo/IA/Jarvis')

from ui.tts_engine import TTSEngine


class TestTTSModelQuality:
    """Tests de priorización de calidad de modelos."""

    def test_get_model_quality_low(self):
        """Test detección de calidad low."""
        tts = TTSEngine(backend="espeak")
        assert tts._get_model_quality("es_MX-claude-low.onnx") == "low"

    def test_get_model_quality_x_low(self):
        """Test detección de calidad x_low."""
        tts = TTSEngine(backend="espeak")
        assert tts._get_model_quality("es_MX-claude-x_low.onnx") == "x_low"

    def test_get_model_quality_medium(self):
        """Test detección de calidad medium."""
        tts = TTSEngine(backend="espeak")
        assert tts._get_model_quality("es_ES-davefx-medium.onnx") == "medium"

    def test_get_model_quality_high(self):
        """Test detección de calidad high."""
        tts = TTSEngine(backend="espeak")
        assert tts._get_model_quality("voice-high.onnx") == "high"

    def test_get_model_quality_unknown(self):
        """Test calidad desconocida."""
        tts = TTSEngine(backend="espeak")
        assert tts._get_model_quality("random-model.onnx") == "unknown"


class TestTTSModelPriority:
    """Tests de prioridad de modelos."""

    def test_priority_order(self):
        """Test orden de prioridad correcto."""
        tts = TTSEngine(backend="espeak")
        priorities = tts.MODEL_QUALITY_PRIORITY

        assert priorities["high"] > priorities["medium"]
        assert priorities["medium"] > priorities["low"]
        assert priorities["low"] > priorities["x_low"]


class TestTTSModelDownload:
    """Tests de descarga de modelos."""

    def test_download_model_invalid_name(self):
        """Test descarga con nombre inválido."""
        tts = TTSEngine(backend="espeak")
        result = tts.download_piper_model("modelo-inexistente")
        assert result == False

    def test_download_model_urls_exist(self):
        """Test que las URLs de descarga están configuradas."""
        tts = TTSEngine(backend="espeak")
        assert "es_MX-claude-low" in tts.PIPER_MODEL_URLS
        assert "es_MX-claude-x_low" in tts.PIPER_MODEL_URLS

    def test_model_info_has_required_fields(self):
        """Test que la info del modelo tiene campos requeridos."""
        tts = TTSEngine(backend="espeak")
        for name, info in tts.PIPER_MODEL_URLS.items():
            assert "onnx" in info
            assert "json" in info
            assert "quality" in info
            assert "size_mb" in info


class TestTTSAvailableModels:
    """Tests de consulta de modelos disponibles."""

    def test_get_available_models_structure(self):
        """Test estructura de respuesta."""
        tts = TTSEngine(backend="espeak")
        models = tts.get_available_models()

        assert "installed" in models
        assert "downloadable" in models
        assert "current_backend" in models
        assert isinstance(models["installed"], list)
        assert isinstance(models["downloadable"], list)

    def test_downloadable_includes_known_models(self):
        """Test que modelos conocidos están en descargables."""
        tts = TTSEngine(backend="espeak")
        models = tts.get_available_models()

        assert "es_MX-claude-low" in models["downloadable"]
        assert "es_MX-claude-x_low" in models["downloadable"]


class TestTTSBackendInfo:
    """Tests de información del backend."""

    def test_backend_info_espeak(self):
        """Test info con backend espeak."""
        tts = TTSEngine(backend="espeak")
        info = tts.get_backend_info()

        assert info["backend"] == "espeak"
        assert "piper_available" in info
        assert "piper_loaded" in info
        assert "model_quality" in info

    def test_backend_info_with_piper(self):
        """Test info con Piper si disponible."""
        tts = TTSEngine(backend="auto")
        info = tts.get_backend_info()

        assert info["backend"] in ["espeak", "piper"]
        # Si Piper está cargado, debe tener info del modelo
        if info["piper_loaded"]:
            assert info["model_quality"] is not None


class TestTTSCleanText:
    """Tests de limpieza de texto para síntesis."""

    def test_clean_removes_emojis(self):
        """Test que remueve emojis."""
        tts = TTSEngine(backend="espeak")
        result = tts._clean_for_speech("Hola 😀 mundo 🎉")
        assert "😀" not in result
        assert "🎉" not in result
        assert "Hola" in result
        assert "mundo" in result

    def test_clean_removes_urls(self):
        """Test que remueve URLs."""
        tts = TTSEngine(backend="espeak")
        result = tts._clean_for_speech("Visita https://example.com para más")
        assert "https" not in result
        assert "example.com" not in result

    def test_clean_removes_markdown(self):
        """Test que remueve formato markdown."""
        tts = TTSEngine(backend="espeak")
        result = tts._clean_for_speech("Texto **negrita** y *cursiva*")
        assert "**" not in result
        assert "*" not in result
        assert "negrita" in result
        assert "cursiva" in result

    def test_clean_normalizes_whitespace(self):
        """Test que normaliza espacios."""
        tts = TTSEngine(backend="espeak")
        result = tts._clean_for_speech("Hola    mundo   test")
        assert "    " not in result
        assert result == "Hola mundo test"


class TestTTSVoiceSettings:
    """Tests de configuración de voz."""

    def test_set_voice(self):
        """Test cambio de voz."""
        tts = TTSEngine(backend="espeak")
        tts.set_voice("en")
        assert tts.espeak_voice == "en"

    def test_set_speed_clamp_min(self):
        """Test límite mínimo de velocidad."""
        tts = TTSEngine(backend="espeak")
        tts.set_speed(50)
        assert tts.espeak_speed == 80

    def test_set_speed_clamp_max(self):
        """Test límite máximo de velocidad."""
        tts = TTSEngine(backend="espeak")
        tts.set_speed(500)
        assert tts.espeak_speed == 450

    def test_set_pitch_clamp_min(self):
        """Test límite mínimo de tono."""
        tts = TTSEngine(backend="espeak")
        tts.set_pitch(-10)
        assert tts.espeak_pitch == 0

    def test_set_pitch_clamp_max(self):
        """Test límite máximo de tono."""
        tts = TTSEngine(backend="espeak")
        tts.set_pitch(120)
        assert tts.espeak_pitch == 99


class TestTTSState:
    """Tests de estado del TTS."""

    def test_initial_not_speaking(self):
        """Test estado inicial."""
        tts = TTSEngine(backend="espeak")
        assert not tts.is_speaking()

    def test_stop_when_not_speaking(self):
        """Test stop cuando no está hablando."""
        tts = TTSEngine(backend="espeak")
        # No debe fallar
        tts.stop()
        assert not tts.is_speaking()


class TestTTSFindModel:
    """Tests de búsqueda de modelos."""

    def test_find_model_empty_dirs(self):
        """Test con directorios vacíos."""
        tts = TTSEngine(backend="espeak")
        # Usar directorios que no existen
        tts.PIPER_MODELS_DIR = Path("/nonexistent/path")
        tts.PIPER_MODELS_DIR_USER = Path("/another/nonexistent")

        result = tts._find_piper_model()
        assert result is None

    def test_find_model_with_mocked_files(self, tmp_path):
        """Test con archivos simulados."""
        tts = TTSEngine(backend="espeak")

        # Crear archivos de modelo simulados
        (tmp_path / "es_MX-claude-low.onnx").touch()
        (tmp_path / "es_MX-claude-low.onnx.json").touch()
        (tmp_path / "es_MX-claude-x_low.onnx").touch()
        (tmp_path / "es_MX-claude-x_low.onnx.json").touch()

        tts.PIPER_MODELS_DIR = Path("/nonexistent")
        tts.PIPER_MODELS_DIR_USER = tmp_path

        result = tts._find_piper_model()
        # Debe seleccionar low sobre x_low (low tiene mayor prioridad)
        assert result is not None
        assert "low" in result.name
        # El modelo seleccionado debe ser claude-low, no claude-x_low
        assert result.name == "es_MX-claude-low.onnx"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
