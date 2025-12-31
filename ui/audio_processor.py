"""
Preprocesamiento de audio para JARVIS.
Filtros y mejoras para mejor reconocimiento de voz.
"""

import numpy as np
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Procesa audio para mejorar reconocimiento de voz."""

    def __init__(self, sample_rate: int = 16000):
        self.sample_rate = sample_rate

        # Configuración de filtros
        self.low_cutoff = 300    # Hz - corta frecuencias bajas (ruido)
        self.high_cutoff = 3400  # Hz - corta frecuencias altas (ruido)

        # Noise gate
        self.noise_threshold = 150   # Umbral de ruido (RMS)
        self.noise_gate_enabled = True

        # Normalización
        self.normalize_enabled = True
        self.target_rms = 3000   # RMS objetivo para normalización

        # Pre-calcular coeficientes del filtro
        self._init_bandpass_filter()

    def _init_bandpass_filter(self):
        """Inicializa coeficientes del filtro pasa-banda."""
        # Filtro Butterworth de orden 2 implementado manualmente
        # para evitar dependencia de scipy
        nyquist = self.sample_rate / 2
        self.low_w = self.low_cutoff / nyquist
        self.high_w = self.high_cutoff / nyquist

        # Estados del filtro (para filtrado en tiempo real)
        self._filter_state_low = np.zeros(2)
        self._filter_state_high = np.zeros(2)

    def process(self, audio_data: np.ndarray) -> np.ndarray:
        """
        Procesa un chunk de audio.

        Args:
            audio_data: Array de int16 con muestras de audio

        Returns:
            Audio procesado como int16
        """
        if len(audio_data) == 0:
            return audio_data

        # Convertir a float para procesamiento
        audio_float = audio_data.astype(np.float32)

        # 1. Filtro pasa-banda (simplificado)
        audio_float = self._apply_bandpass(audio_float)

        # 2. Noise gate
        if self.noise_gate_enabled:
            audio_float = self._apply_noise_gate(audio_float)

        # 3. Normalización
        if self.normalize_enabled:
            audio_float = self._normalize(audio_float)

        # Convertir de vuelta a int16
        audio_float = np.clip(audio_float, -32768, 32767)
        return audio_float.astype(np.int16)

    def _apply_bandpass(self, audio: np.ndarray) -> np.ndarray:
        """Aplica filtro pasa-banda simple usando promedio móvil."""
        # Filtro pasa-altos simple (elimina DC y bajas frecuencias)
        # Usando diferencia de promedios móviles
        if len(audio) < 10:
            return audio

        # Tamaño de ventana basado en frecuencias de corte
        window_low = max(2, int(self.sample_rate / self.low_cutoff / 4))
        window_high = max(2, int(self.sample_rate / self.high_cutoff / 4))

        # Pasa-altos: restar promedio móvil largo
        if window_low < len(audio):
            kernel_low = np.ones(window_low) / window_low
            low_freq = np.convolve(audio, kernel_low, mode='same')
            audio = audio - low_freq * 0.8  # Atenuar bajas frecuencias

        # Pasa-bajos: promedio móvil corto
        if window_high < len(audio):
            kernel_high = np.ones(window_high) / window_high
            audio = np.convolve(audio, kernel_high, mode='same')

        return audio

    def _apply_noise_gate(self, audio: np.ndarray) -> np.ndarray:
        """Aplica noise gate para eliminar ruido de fondo."""
        rms = np.sqrt(np.mean(audio ** 2))

        if rms < self.noise_threshold:
            # Audio bajo el umbral - atenuar fuertemente
            return audio * 0.1
        else:
            # Audio sobre el umbral - pasar con atenuación suave del ruido
            # Soft knee: transición suave
            ratio = min(1.0, (rms - self.noise_threshold * 0.5) / (self.noise_threshold * 0.5))
            return audio * ratio

    def _normalize(self, audio: np.ndarray) -> np.ndarray:
        """Normaliza el volumen del audio."""
        rms = np.sqrt(np.mean(audio ** 2))

        if rms < 1:  # Evitar división por cero
            return audio

        # Calcular ganancia necesaria
        gain = self.target_rms / rms

        # Limitar ganancia para evitar amplificar ruido
        gain = min(gain, 4.0)  # Máximo 4x amplificación
        gain = max(gain, 0.25)  # Mínimo 0.25x atenuación

        return audio * gain

    def set_noise_threshold(self, threshold: int):
        """Ajusta umbral de noise gate."""
        self.noise_threshold = max(50, min(1000, threshold))

    def set_normalize_target(self, target: int):
        """Ajusta nivel objetivo de normalización."""
        self.target_rms = max(1000, min(10000, target))

    def enable_noise_gate(self, enabled: bool):
        """Habilita/deshabilita noise gate."""
        self.noise_gate_enabled = enabled

    def enable_normalize(self, enabled: bool):
        """Habilita/deshabilita normalización."""
        self.normalize_enabled = enabled

    def get_stats(self, audio: np.ndarray) -> dict:
        """Retorna estadísticas del audio."""
        if len(audio) == 0:
            return {"rms": 0, "peak": 0, "snr": 0}

        audio_float = audio.astype(np.float32)
        rms = np.sqrt(np.mean(audio_float ** 2))
        peak = np.max(np.abs(audio_float))

        return {
            "rms": int(rms),
            "peak": int(peak),
            "is_speech": rms > self.noise_threshold
        }
