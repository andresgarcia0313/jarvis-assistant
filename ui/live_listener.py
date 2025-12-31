"""
Live STT listener - escucha continua sin tokens.
Solo usa Vosk local para transcribir en tiempo real.
"""

import queue
import threading
import logging
import time
from typing import Callable, Optional

import numpy as np
import sounddevice as sd
import json
from vosk import Model, KaldiRecognizer, SetLogLevel
from ui.audio_processor import AudioProcessor
from ui.vad_detector import VADDetector
from ui.beamformer import Beamformer

logger = logging.getLogger(__name__)


class LiveListener:
    """Escucha continua con Vosk, sin consumir tokens."""

    # Timeout de silencio para forzar finalización (segundos)
    SILENCE_TIMEOUT = 1.2  # Reducido para respuesta más rápida
    # Umbral de nivel de audio para considerar "silencio"
    SILENCE_THRESHOLD = 8  # Aumentado para mejor detección de fin de frase

    def __init__(self, model_path: str, sample_rate: int = 16000, device: Optional[int] = None):
        self.sample_rate = sample_rate
        self.device = device  # None = usar default del sistema
        self.audio_queue: queue.Queue = queue.Queue()
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_level = 0
        self._audio_level_raw = 0  # Nivel sin procesar
        self._last_speech_time = 0.0
        self._last_partial = ""

        # Preprocesador de audio
        self.audio_processor = AudioProcessor(sample_rate)
        self.preprocessing_enabled = True

        # VAD (Voice Activity Detection)
        self.vad = VADDetector(sample_rate, aggressiveness=2)
        self.vad_enabled = True
        self._is_speech_active = False

        # Beamforming (si hay 2+ micrófonos)
        self.beamformer = Beamformer(sample_rate)
        self.beamforming_enabled = False  # Se habilita si el dispositivo tiene 2+ canales
        self._num_channels = 1

        SetLogLevel(-1)
        logger.info(f"Cargando modelo Vosk: {model_path}")
        self.model = Model(model_path)
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)
        # Configurar para mejor detección de palabras cortas
        self.recognizer.SetMaxAlternatives(0)  # Solo mejor resultado

    def set_device(self, device_index: Optional[int]):
        """Cambia el dispositivo de audio (requiere reiniciar listener)."""
        self.device = device_index
        logger.info(f"Dispositivo de audio: {device_index}")

    def set_preprocessing(self, enabled: bool):
        """Habilita/deshabilita preprocesamiento de audio."""
        self.preprocessing_enabled = enabled
        logger.info(f"Preprocesamiento: {'activado' if enabled else 'desactivado'}")

    def _audio_callback(self, indata, frames, time_info, status):
        if status:
            logger.warning(f"Audio: {status}")

        # Convertir a numpy array
        audio_data = np.frombuffer(indata, dtype=np.int16).copy()

        # Si tenemos 2 canales, aplicar beamforming
        if self._num_channels == 2 and self.beamforming_enabled:
            # Reshape a estéreo (samples, 2)
            audio_stereo = audio_data.reshape(-1, 2)
            # Aplicar beamforming para obtener mono enfocado
            audio_data = self.beamformer.process(audio_stereo).astype(np.int16)

        # Calcular nivel de audio raw (antes de procesar)
        rms_raw = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        self._audio_level_raw = min(100, int(rms_raw / 300 * 100))

        # Preprocesar audio si está habilitado
        if self.preprocessing_enabled:
            audio_data = self.audio_processor.process(audio_data)

        # Calcular nivel de audio procesado
        rms = np.sqrt(np.mean(audio_data.astype(np.float32) ** 2))
        self._audio_level = min(100, int(rms / 300 * 100))

        # Detectar voz con VAD
        audio_bytes = audio_data.tobytes()
        if self.vad_enabled and self.vad.is_enabled():
            self._is_speech_active = self.vad.is_speech(audio_bytes)
        else:
            self._is_speech_active = self._audio_level > self.SILENCE_THRESHOLD

        # Enviar audio procesado a la cola
        self.audio_queue.put(audio_bytes)

    def start(self, on_text: Callable[[str, bool], None]):
        """
        Inicia escucha continua.
        on_text(texto, es_final): callback con texto y si es resultado final.
        """
        if self.running:
            return

        self.running = True
        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(on_text,),
            daemon=True
        )
        self._thread.start()

    def _detect_channels(self) -> int:
        """Detecta el número de canales del dispositivo de audio."""
        try:
            if self.device is not None:
                device_info = sd.query_devices(self.device)
            else:
                device_info = sd.query_devices(kind='input')
            max_channels = int(device_info.get('max_input_channels', 1))
            return min(max_channels, 2)  # Máximo 2 canales para beamforming
        except Exception as e:
            logger.warning(f"Error detectando canales: {e}")
            return 1

    def _listen_loop(self, on_text: Callable[[str, bool], None]):
        try:
            # Detectar número de canales disponibles
            self._num_channels = self._detect_channels()
            self.beamforming_enabled = self._num_channels >= 2

            if self.beamforming_enabled:
                logger.info(f"Beamforming habilitado: {self._num_channels} canales")
                self.beamformer.enable(True)
            else:
                logger.info("Beamforming deshabilitado: solo 1 canal disponible")

            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=2048,  # Aumentado para mejor buffer
                dtype='int16',
                channels=self._num_channels,
                device=self.device,  # Usar dispositivo configurado
                callback=self._audio_callback
            ):
                while self.running:
                    try:
                        data = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        # Verificar timeout de silencio
                        self._check_silence_timeout(on_text)
                        continue

                    now = time.time()

                    try:
                        if self.recognizer.AcceptWaveform(data):
                            result = json.loads(self.recognizer.Result())
                            text = result.get("text", "").strip()
                            if text:
                                self._last_partial = ""
                                self._last_speech_time = 0
                                on_text(text, True)
                        else:
                            partial = json.loads(self.recognizer.PartialResult())
                            text = partial.get("partial", "").strip()
                            if text:
                                # Actualizar tiempo de última detección de voz
                                if text != self._last_partial:
                                    self._last_speech_time = now
                                    self._last_partial = text
                                on_text(text, False)
                    except json.JSONDecodeError:
                        continue  # Ignorar errores de parsing

                    # Verificar timeout después de procesar
                    self._check_silence_timeout(on_text)

        except Exception as e:
            logger.error(f"Error en listener: {e}")
        finally:
            self.running = False

    def _check_silence_timeout(self, on_text: Callable[[str, bool], None]):
        """Verifica si hay silencio prolongado y fuerza finalización."""
        if not self._last_partial or self._last_speech_time == 0:
            return

        now = time.time()
        silence_duration = now - self._last_speech_time

        # Usar VAD para detección de silencio si está disponible
        if self.vad_enabled and self.vad.is_enabled():
            is_silent = not self._is_speech_active
        else:
            is_silent = self._audio_level < self.SILENCE_THRESHOLD

        # Si hay silencio por más del timeout y tenemos texto parcial
        if is_silent and silence_duration >= self.SILENCE_TIMEOUT:
            logger.info(f"Timeout de silencio: finalizando '{self._last_partial}'")
            final_text = self._last_partial
            self._last_partial = ""
            self._last_speech_time = 0
            # Forzar reset del recognizer para limpiar estado
            self.recognizer.Reset()
            on_text(final_text, True)

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def is_running(self) -> bool:
        return self.running

    def get_audio_level(self) -> int:
        return self._audio_level

    def set_beamforming(self, enabled: bool):
        """Habilita/deshabilita beamforming (requiere 2+ canales)."""
        if self._num_channels >= 2:
            self.beamforming_enabled = enabled
            self.beamformer.enable(enabled)
            logger.info(f"Beamforming: {'activado' if enabled else 'desactivado'}")
        else:
            logger.warning("Beamforming no disponible: se requieren 2+ canales")

    def set_beamformer_direction(self, angle: float):
        """Cambia el ángulo de enfoque del beamformer (-90 a 90 grados)."""
        self.beamformer.set_direction(angle)

    def is_beamforming_available(self) -> bool:
        """Retorna si el beamforming está disponible (2+ canales)."""
        return self._num_channels >= 2

    def is_beamforming_enabled(self) -> bool:
        """Retorna si el beamforming está activo."""
        return self.beamforming_enabled and self.beamformer.is_enabled()

    def get_beamformer_info(self) -> dict:
        """Retorna información del beamformer."""
        info = self.beamformer.get_info()
        info["available"] = self._num_channels >= 2
        info["num_channels"] = self._num_channels
        return info
