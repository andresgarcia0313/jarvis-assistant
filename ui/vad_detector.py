"""
Voice Activity Detection para JARVIS.
Usa WebRTC VAD para detectar cuando hay voz activa.
"""

import logging
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)

try:
    import webrtcvad
    WEBRTC_VAD_AVAILABLE = True
except ImportError:
    WEBRTC_VAD_AVAILABLE = False
    logger.warning("webrtcvad no disponible")


class VADDetector:
    """Detector de actividad de voz usando WebRTC VAD."""

    def __init__(self, sample_rate: int = 16000, aggressiveness: int = 2):
        """
        Inicializa el detector VAD.

        Args:
            sample_rate: Frecuencia de muestreo (8000, 16000, 32000, 48000)
            aggressiveness: Nivel de agresividad (0-3)
                0: Menos agresivo, más sensible a voz
                3: Más agresivo, filtra más ruido
        """
        self.sample_rate = sample_rate
        self.aggressiveness = aggressiveness
        self._vad: Optional['webrtcvad.Vad'] = None
        self._enabled = False

        # Buffer para suavizar detección (evitar parpadeo)
        self._history = deque(maxlen=10)  # Últimos 10 frames
        self._speech_threshold = 0.6  # 60% de frames con voz = hay voz

        # Tamaño de frame requerido por WebRTC VAD (10, 20, o 30 ms)
        self._frame_duration_ms = 30
        self._frame_size = int(sample_rate * self._frame_duration_ms / 1000)

        self._init_vad()

    def _init_vad(self):
        """Inicializa WebRTC VAD."""
        if not WEBRTC_VAD_AVAILABLE:
            logger.warning("WebRTC VAD no disponible")
            return

        try:
            self._vad = webrtcvad.Vad(self.aggressiveness)
            self._enabled = True
            logger.info(f"VAD inicializado (agresividad={self.aggressiveness})")
        except Exception as e:
            logger.error(f"Error inicializando VAD: {e}")
            self._vad = None
            self._enabled = False

    def is_speech(self, audio_data: bytes) -> bool:
        """
        Detecta si hay voz en el chunk de audio.

        Args:
            audio_data: Bytes de audio (int16, mono)

        Returns:
            True si hay voz detectada
        """
        if not self._enabled or not self._vad:
            return True  # Si VAD no está disponible, asumir que hay voz

        try:
            # WebRTC VAD necesita frames de tamaño específico
            # Procesar el audio en frames
            num_frames = len(audio_data) // (self._frame_size * 2)  # *2 porque int16

            if num_frames == 0:
                return self._get_smoothed_result(False)

            speech_frames = 0
            for i in range(num_frames):
                start = i * self._frame_size * 2
                end = start + self._frame_size * 2
                frame = audio_data[start:end]

                if len(frame) == self._frame_size * 2:
                    try:
                        if self._vad.is_speech(frame, self.sample_rate):
                            speech_frames += 1
                    except Exception:
                        pass

            # Si más de la mitad de los frames tienen voz
            has_speech = (speech_frames / max(1, num_frames)) > 0.5
            return self._get_smoothed_result(has_speech)

        except Exception as e:
            logger.error(f"Error en VAD: {e}")
            return True

    def _get_smoothed_result(self, current: bool) -> bool:
        """Suaviza el resultado usando historial."""
        self._history.append(1 if current else 0)

        if len(self._history) < 3:
            return current

        # Calcular promedio del historial
        avg = sum(self._history) / len(self._history)
        return avg >= self._speech_threshold

    def set_aggressiveness(self, level: int):
        """Cambia el nivel de agresividad (0-3)."""
        level = max(0, min(3, level))
        if self._vad and level != self.aggressiveness:
            self.aggressiveness = level
            self._vad.set_mode(level)
            logger.info(f"VAD agresividad: {level}")

    def set_threshold(self, threshold: float):
        """Cambia el umbral de detección (0.0-1.0)."""
        self._speech_threshold = max(0.1, min(0.9, threshold))

    def reset(self):
        """Resetea el historial."""
        self._history.clear()

    def is_enabled(self) -> bool:
        """Retorna si VAD está habilitado."""
        return self._enabled

    def get_frame_size(self) -> int:
        """Retorna el tamaño de frame requerido."""
        return self._frame_size
