"""
Gestión de dispositivos de audio para JARVIS.
Permite detectar y seleccionar micrófonos.
"""

import sounddevice as sd
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AudioDeviceManager:
    """Gestiona dispositivos de audio del sistema."""

    def __init__(self):
        self._devices = []
        self._input_devices = []
        self.refresh()

    def refresh(self):
        """Actualiza la lista de dispositivos."""
        try:
            self._devices = sd.query_devices()
            self._input_devices = [
                d for d in self._devices
                if d['max_input_channels'] > 0
            ]
        except Exception as e:
            logger.error(f"Error obteniendo dispositivos: {e}")
            self._devices = []
            self._input_devices = []

    def get_input_devices(self) -> List[Dict]:
        """Retorna lista de dispositivos de entrada (micrófonos)."""
        return [
            {
                'index': i,
                'name': d['name'],
                'channels': d['max_input_channels'],
                'sample_rate': int(d['default_samplerate']),
                'is_default': i == sd.default.device[0]
            }
            for i, d in enumerate(self._devices)
            if d['max_input_channels'] > 0
        ]

    def get_default_input(self) -> Optional[int]:
        """Retorna índice del dispositivo de entrada por defecto."""
        try:
            return sd.default.device[0]
        except:
            return None

    def get_best_microphone(self) -> Optional[int]:
        """
        Selecciona el mejor micrófono disponible.
        Prioriza: alta tasa de muestreo, múltiples canales.
        """
        inputs = self.get_input_devices()
        if not inputs:
            return None

        # Ordenar por: sample_rate (desc), channels (desc)
        scored = []
        for dev in inputs:
            score = dev['sample_rate'] + (dev['channels'] * 1000)
            # Bonus si tiene "array" o "mic" en el nombre (mejor para voz)
            name_lower = dev['name'].lower()
            if 'array' in name_lower:
                score += 5000  # Micrófonos array son mejores para voz
            if 'headset' in name_lower or 'auricular' in name_lower:
                score += 3000  # Headsets suelen tener mejor SNR
            scored.append((score, dev['index']))

        scored.sort(reverse=True)
        return scored[0][1] if scored else None

    def set_default_input(self, device_index: int) -> bool:
        """Establece el dispositivo de entrada por defecto."""
        try:
            sd.default.device[0] = device_index
            return True
        except Exception as e:
            logger.error(f"Error estableciendo dispositivo: {e}")
            return False

    def test_device(self, device_index: int, duration: float = 0.5) -> float:
        """
        Prueba un dispositivo y retorna el nivel de ruido promedio.
        Útil para detectar micrófonos con mucho ruido de fondo.
        """
        import numpy as np

        try:
            recording = sd.rec(
                int(duration * 16000),
                samplerate=16000,
                channels=1,
                dtype='int16',
                device=device_index
            )
            sd.wait()
            rms = np.sqrt(np.mean(recording.astype(np.float32) ** 2))
            return float(rms)
        except Exception as e:
            logger.error(f"Error probando dispositivo {device_index}: {e}")
            return -1

    def format_device_list(self) -> str:
        """Formatea la lista de dispositivos para mostrar."""
        lines = ["Dispositivos de entrada disponibles:"]
        for dev in self.get_input_devices():
            default = " (DEFAULT)" if dev['is_default'] else ""
            lines.append(
                f"  [{dev['index']}] {dev['name']} "
                f"({dev['channels']}ch, {dev['sample_rate']}Hz){default}"
            )
        return "\n".join(lines)


def get_device_manager() -> AudioDeviceManager:
    """Singleton para el gestor de dispositivos."""
    if not hasattr(get_device_manager, '_instance'):
        get_device_manager._instance = AudioDeviceManager()
    return get_device_manager._instance
