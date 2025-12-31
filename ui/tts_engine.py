"""
Motor TTS para JARVIS - Síntesis de voz local.
Soporta múltiples backends: espeak-ng (básico) y Piper (alta calidad)
"""

import subprocess
import threading
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Intentar importar piper
try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    logger.info("Piper no disponible, usando espeak-ng")


class TTSEngine:
    """Motor de síntesis de voz con múltiples backends."""

    # Ruta donde buscar modelos Piper
    PIPER_MODELS_DIR = Path("/usr/share/jarvis/models/piper")
    PIPER_MODELS_DIR_USER = Path.home() / ".local/share/jarvis/models/piper"

    def __init__(self, backend: str = "auto"):
        """
        Inicializa el motor TTS.

        Args:
            backend: "auto" (detecta mejor disponible), "piper", o "espeak"
        """
        self._speaking = False
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._piper_voice: Optional['PiperVoice'] = None

        # Configuración espeak-ng
        self.espeak_voice = "es"  # Español
        self.espeak_speed = 160   # Palabras por minuto (default 175)
        self.espeak_pitch = 45    # Tono (default 50, más bajo = más grave)

        # Seleccionar backend
        if backend == "auto":
            self.backend = self._detect_best_backend()
        else:
            self.backend = backend

        logger.info(f"TTS backend: {self.backend}")

    def _detect_best_backend(self) -> str:
        """Detecta el mejor backend disponible."""
        # Intentar Piper primero
        if PIPER_AVAILABLE:
            model_path = self._find_piper_model()
            if model_path:
                try:
                    self._piper_voice = PiperVoice.load(str(model_path))
                    logger.info(f"Piper cargado: {model_path}")
                    return "piper"
                except Exception as e:
                    logger.warning(f"Error cargando Piper: {e}")

        # Fallback a espeak-ng
        return "espeak"

    # Prioridad de calidad de modelos (mayor = mejor)
    MODEL_QUALITY_PRIORITY = {
        "high": 4,
        "medium": 3,
        "low": 2,
        "x_low": 1,
        "x-low": 1,
    }

    # URLs de modelos Piper en español para descarga automática
    PIPER_MODEL_URLS = {
        "es_MX-claude-low": {
            "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/low/es_MX-claude-low.onnx",
            "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/low/es_MX-claude-low.onnx.json",
            "quality": "low",
            "size_mb": 40
        },
        "es_MX-claude-x_low": {
            "onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/x_low/es_MX-claude-x_low.onnx",
            "json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_MX/claude/x_low/es_MX-claude-x_low.onnx.json",
            "quality": "x_low",
            "size_mb": 20
        }
    }

    def _find_piper_model(self) -> Optional[Path]:
        """Busca un modelo Piper instalado, priorizando mejor calidad."""
        search_dirs = [self.PIPER_MODELS_DIR, self.PIPER_MODELS_DIR_USER]
        found_models = []

        for dir_path in search_dirs:
            if dir_path.exists():
                # Buscar archivos .onnx
                for onnx_file in dir_path.glob("*.onnx"):
                    json_file = onnx_file.with_suffix(".onnx.json")
                    if json_file.exists():
                        # Determinar calidad del modelo por el nombre
                        quality = self._get_model_quality(onnx_file.name)
                        found_models.append((onnx_file, quality))

        if not found_models:
            return None

        # Ordenar por calidad (mayor primero)
        found_models.sort(key=lambda x: self.MODEL_QUALITY_PRIORITY.get(x[1], 0), reverse=True)

        best_model = found_models[0][0]
        logger.info(f"Modelo Piper seleccionado: {best_model.name} (calidad: {found_models[0][1]})")
        return best_model

    def _get_model_quality(self, model_name: str) -> str:
        """Extrae la calidad del nombre del modelo."""
        name_lower = model_name.lower()
        # Orden de búsqueda: más específico primero (x_low antes de low)
        for quality in ["x_low", "x-low", "high", "medium", "low"]:
            if quality in name_lower:
                return quality
        return "unknown"

    def download_piper_model(self, model_name: str = "es_MX-claude-low") -> bool:
        """
        Descarga un modelo Piper.

        Args:
            model_name: Nombre del modelo a descargar

        Returns:
            True si se descargó correctamente
        """
        if model_name not in self.PIPER_MODEL_URLS:
            logger.error(f"Modelo no reconocido: {model_name}")
            return False

        model_info = self.PIPER_MODEL_URLS[model_name]

        # Crear directorio de usuario si no existe
        self.PIPER_MODELS_DIR_USER.mkdir(parents=True, exist_ok=True)

        onnx_path = self.PIPER_MODELS_DIR_USER / f"{model_name}.onnx"
        json_path = self.PIPER_MODELS_DIR_USER / f"{model_name}.onnx.json"

        try:
            import urllib.request

            logger.info(f"Descargando modelo Piper '{model_name}' ({model_info['size_mb']}MB)...")

            # Descargar .onnx
            urllib.request.urlretrieve(model_info["onnx"], onnx_path)

            # Descargar .json
            urllib.request.urlretrieve(model_info["json"], json_path)

            logger.info(f"Modelo descargado en: {self.PIPER_MODELS_DIR_USER}")
            return True

        except Exception as e:
            logger.error(f"Error descargando modelo: {e}")
            # Limpiar archivos parciales
            if onnx_path.exists():
                onnx_path.unlink()
            if json_path.exists():
                json_path.unlink()
            return False

    def get_available_models(self) -> dict:
        """Retorna información sobre modelos disponibles."""
        installed = []
        search_dirs = [self.PIPER_MODELS_DIR, self.PIPER_MODELS_DIR_USER]

        for dir_path in search_dirs:
            if dir_path.exists():
                for onnx_file in dir_path.glob("*.onnx"):
                    json_file = onnx_file.with_suffix(".onnx.json")
                    if json_file.exists():
                        quality = self._get_model_quality(onnx_file.name)
                        installed.append({
                            "name": onnx_file.stem,
                            "path": str(onnx_file),
                            "quality": quality
                        })

        return {
            "installed": installed,
            "downloadable": list(self.PIPER_MODEL_URLS.keys()),
            "current_backend": self.backend
        }

    def speak(self, text: str, on_complete: Optional[Callable] = None):
        """Sintetiza y reproduce texto en un hilo separado."""
        if self._speaking:
            self.stop()

        self._thread = threading.Thread(
            target=self._speak_thread,
            args=(text, on_complete),
            daemon=True
        )
        self._thread.start()

    def _speak_thread(self, text: str, on_complete: Optional[Callable]):
        """Hilo de síntesis de voz."""
        self._speaking = True
        try:
            if self.backend == "piper" and self._piper_voice:
                self._speak_piper(text)
            else:
                self._speak_espeak(text)
        except Exception as e:
            logger.error(f"Error TTS: {e}")
        finally:
            self._speaking = False
            self._process = None
            if on_complete:
                on_complete()

    def _speak_piper(self, text: str):
        """Síntesis con Piper TTS (alta calidad)."""
        if not self._piper_voice:
            logger.warning("Piper no inicializado, usando espeak")
            self._speak_espeak(text)
            return

        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return

        try:
            import wave
            import sounddevice as sd
            import numpy as np

            # Generar audio con Piper
            audio_data = []
            for audio_chunk in self._piper_voice.synthesize_stream_raw(clean_text):
                audio_data.append(audio_chunk)

            if not audio_data:
                return

            # Concatenar chunks
            full_audio = b''.join(audio_data)

            # Convertir a numpy array (Piper genera int16 @ 22050Hz)
            audio_np = np.frombuffer(full_audio, dtype=np.int16)

            # Reproducir
            sd.play(audio_np, samplerate=22050)
            sd.wait()

        except Exception as e:
            logger.error(f"Error en Piper: {e}, usando espeak")
            self._speak_espeak(text)

    def _speak_espeak(self, text: str):
        """Síntesis con espeak-ng."""
        # Limpiar texto para espeak
        clean_text = self._clean_for_speech(text)
        if not clean_text:
            return

        cmd = [
            "espeak-ng",
            "-v", self.espeak_voice,
            "-s", str(self.espeak_speed),
            "-p", str(self.espeak_pitch),
            clean_text
        ]

        try:
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self._process.wait()
        except FileNotFoundError:
            logger.error("espeak-ng no está instalado")
        except Exception as e:
            logger.error(f"Error ejecutando espeak-ng: {e}")

    def _clean_for_speech(self, text: str) -> str:
        """Limpia texto para síntesis de voz."""
        # Remover emojis y caracteres especiales
        import re

        # Remover emojis
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)

        # Remover caracteres de formato
        text = re.sub(r'[►◆⟩🤖💭⚠✓✗]', '', text)

        # Remover URLs
        text = re.sub(r'https?://\S+', '', text)

        # Remover markdown
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # **bold**
        text = re.sub(r'\*([^*]+)\*', r'\1', text)      # *italic*
        text = re.sub(r'`([^`]+)`', r'\1', text)        # `code`

        # Limpiar espacios
        text = ' '.join(text.split())

        return text.strip()

    def stop(self):
        """Detiene la síntesis actual."""
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._speaking = False

    def is_speaking(self) -> bool:
        """Retorna True si está hablando."""
        return self._speaking

    def set_voice(self, voice: str):
        """Cambia la voz (ej: 'es', 'es-la', 'en')."""
        self.espeak_voice = voice

    def set_speed(self, speed: int):
        """Cambia velocidad (80-450 palabras/min)."""
        self.espeak_speed = max(80, min(450, speed))

    def set_pitch(self, pitch: int):
        """Cambia tono (0-99)."""
        self.espeak_pitch = max(0, min(99, pitch))

    def get_backend_info(self) -> dict:
        """Retorna información del backend actual."""
        info = {
            "backend": self.backend,
            "piper_available": PIPER_AVAILABLE,
            "piper_loaded": self._piper_voice is not None,
            "model_quality": None
        }

        # Obtener calidad del modelo cargado
        if self._piper_voice is not None:
            model_path = self._find_piper_model()
            if model_path:
                info["model_quality"] = self._get_model_quality(model_path.name)
                info["model_name"] = model_path.stem

        return info
