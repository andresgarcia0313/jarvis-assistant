"""
Beamforming para JARVIS.
Usa Delay-and-Sum Beamforming con 2 micrófonos para enfocar en la dirección del usuario.
"""

import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class Beamformer:
    """
    Beamformer de Delay-and-Sum para 2 micrófonos.

    Enfoca la captura de audio en una dirección específica,
    atenuando sonidos de otras direcciones.
    """

    # Velocidad del sonido en aire (m/s)
    SPEED_OF_SOUND = 343.0

    def __init__(
        self,
        sample_rate: int = 16000,
        mic_distance: float = 0.1,  # 10cm típico en laptops
        direction_angle: float = 0.0  # 0 = frente, -90 = izquierda, 90 = derecha
    ):
        """
        Inicializa el beamformer.

        Args:
            sample_rate: Frecuencia de muestreo
            mic_distance: Distancia entre micrófonos en metros
            direction_angle: Ángulo de enfoque en grados (-90 a 90)
        """
        self.sample_rate = sample_rate
        self.mic_distance = mic_distance
        self.direction_angle = direction_angle
        self._enabled = False

        # Calcular delay inicial
        self._calculate_delay()

        logger.info(f"Beamformer inicializado: {mic_distance*100:.1f}cm, {direction_angle}°")

    def _calculate_delay(self):
        """Calcula el delay necesario para el ángulo dado."""
        # Convertir ángulo a radianes
        angle_rad = np.radians(self.direction_angle)

        # Calcular delay de tiempo (segundos)
        # El sonido desde un ángulo llega con diferencia de tiempo a cada mic
        time_delay = self.mic_distance * np.sin(angle_rad) / self.SPEED_OF_SOUND

        # Convertir a samples
        self._delay_samples = int(abs(time_delay * self.sample_rate))
        self._delay_direction = 1 if time_delay >= 0 else -1

        logger.debug(f"Delay calculado: {self._delay_samples} samples, dir={self._delay_direction}")

    def set_direction(self, angle: float):
        """
        Cambia el ángulo de enfoque.

        Args:
            angle: Ángulo en grados (-90 a 90)
        """
        self.direction_angle = max(-90, min(90, angle))
        self._calculate_delay()

    def set_mic_distance(self, distance: float):
        """
        Cambia la distancia entre micrófonos.

        Args:
            distance: Distancia en metros
        """
        self.mic_distance = max(0.01, min(1.0, distance))
        self._calculate_delay()

    def process(self, audio_stereo: np.ndarray) -> np.ndarray:
        """
        Aplica beamforming a audio estéreo.

        Args:
            audio_stereo: Array de shape (samples, 2) con audio de 2 micrófonos

        Returns:
            Array mono con audio procesado
        """
        if len(audio_stereo.shape) != 2 or audio_stereo.shape[1] != 2:
            # Si no es estéreo, retornar sin procesar
            if len(audio_stereo.shape) == 1:
                return audio_stereo
            return audio_stereo[:, 0]

        left = audio_stereo[:, 0].astype(np.float32)
        right = audio_stereo[:, 1].astype(np.float32)

        # Aplicar delay al canal apropiado
        if self._delay_samples > 0:
            if self._delay_direction > 0:
                # Delay en canal derecho
                right_delayed = np.zeros_like(right)
                right_delayed[self._delay_samples:] = right[:-self._delay_samples]
                right = right_delayed
            else:
                # Delay en canal izquierdo
                left_delayed = np.zeros_like(left)
                left_delayed[self._delay_samples:] = left[:-self._delay_samples]
                left = left_delayed

        # Delay-and-Sum: promediar los canales alineados
        output = (left + right) / 2.0

        return output.astype(audio_stereo.dtype)

    def process_separate_channels(
        self,
        left: np.ndarray,
        right: np.ndarray
    ) -> np.ndarray:
        """
        Aplica beamforming a canales separados.

        Args:
            left: Audio del micrófono izquierdo
            right: Audio del micrófono derecho

        Returns:
            Array mono con audio procesado
        """
        # Crear array estéreo temporal
        stereo = np.column_stack([left, right])
        return self.process(stereo)

    def estimate_direction(self, audio_stereo: np.ndarray) -> float:
        """
        Estima la dirección del sonido dominante.

        Usa correlación cruzada para encontrar el delay entre canales.

        Args:
            audio_stereo: Array de shape (samples, 2)

        Returns:
            Ángulo estimado en grados
        """
        if len(audio_stereo.shape) != 2 or audio_stereo.shape[1] != 2:
            return 0.0

        left = audio_stereo[:, 0].astype(np.float32)
        right = audio_stereo[:, 1].astype(np.float32)

        # Correlación cruzada
        correlation = np.correlate(left, right, mode='full')
        max_idx = np.argmax(correlation)
        delay_samples = max_idx - len(left) + 1

        # Convertir delay a ángulo
        max_delay = int(self.mic_distance * self.sample_rate / self.SPEED_OF_SOUND)
        if max_delay == 0:
            return 0.0

        delay_samples = np.clip(delay_samples, -max_delay, max_delay)
        angle_rad = np.arcsin(delay_samples * self.SPEED_OF_SOUND /
                              (self.mic_distance * self.sample_rate))

        return np.degrees(angle_rad)

    def enable(self, enabled: bool = True):
        """Habilita/deshabilita el beamformer."""
        self._enabled = enabled
        logger.info(f"Beamformer: {'activado' if enabled else 'desactivado'}")

    def is_enabled(self) -> bool:
        """Retorna si el beamformer está habilitado."""
        return self._enabled

    def get_info(self) -> dict:
        """Retorna información del beamformer."""
        return {
            "enabled": self._enabled,
            "mic_distance_cm": self.mic_distance * 100,
            "direction_angle": self.direction_angle,
            "delay_samples": self._delay_samples
        }
