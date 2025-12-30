"""
JARVIS Wake Word Detection Module
Uses OpenWakeWord for local, offline wake word detection
"""

import threading
import queue
import logging
from typing import Callable, Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

try:
    from openwakeword.model import Model as OWWModel
    OPENWAKEWORD_AVAILABLE = True
except ImportError:
    OPENWAKEWORD_AVAILABLE = False
    logger.warning("OpenWakeWord not available")


class WakeWordDetector:
    """OpenWakeWord-based wake word detector."""

    def __init__(
        self,
        model_name: str = "hey_jarvis_v0.1",
        threshold: float = 0.5,
        sample_rate: int = 16000,
        fallback_model: str = "alexa_v0.1"
    ):
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.is_listening = False
        self._stop_requested = False
        self.audio_queue: queue.Queue = queue.Queue()

        if not OPENWAKEWORD_AVAILABLE:
            raise RuntimeError(
                "OpenWakeWord not installed. "
                "Install with: pip install openwakeword"
            )

        # Try to load custom model, fallback to built-in
        try:
            logger.info(f"Loading wake word model: {model_name}")
            self.model = OWWModel(
                wakeword_models=[model_name],
                inference_framework="onnx"
            )
            self.model_name = model_name
        except Exception as e:
            logger.warning(f"Custom model '{model_name}' not found: {e}")
            logger.info(f"Using fallback model: {fallback_model}")
            self.model = OWWModel(
                wakeword_models=[fallback_model],
                inference_framework="onnx"
            )
            self.model_name = fallback_model

        logger.info("Wake word detector initialized")

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio status: {status}")
        # OpenWakeWord expects int16
        audio_int16 = (indata * 32767).astype(np.int16)
        self.audio_queue.put(audio_int16.flatten())

    def listen(
        self,
        on_detection: Callable[[], None],
        interrupt_check: Optional[Callable[[], bool]] = None
    ):
        """
        Listen for wake word continuously.

        Args:
            on_detection: Callback when wake word is detected
            interrupt_check: Function that returns True to stop listening
        """
        self.is_listening = True
        self._stop_requested = False
        self.audio_queue = queue.Queue()

        # OpenWakeWord needs 1280 samples (80ms at 16kHz) per prediction
        chunk_size = 1280

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32',
                blocksize=chunk_size,
                callback=self._audio_callback
            ):
                logger.info(f"Listening for wake word: '{self.model_name}'")

                while self.is_listening and not self._stop_requested:
                    if interrupt_check and interrupt_check():
                        break

                    try:
                        audio_chunk = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    # Run prediction
                    prediction = self.model.predict(audio_chunk)

                    # Check if any model triggered
                    for model_name, scores in prediction.items():
                        if isinstance(scores, (float, np.floating)):
                            score = scores
                        else:
                            score = scores[-1] if len(scores) > 0 else 0

                        if score >= self.threshold:
                            logger.info(f"Wake word detected! Score: {score:.3f}")
                            # Reset model state
                            self.model.reset()
                            on_detection()
                            break

        except Exception as e:
            logger.error(f"Error in wake word detection: {e}")
        finally:
            self.is_listening = False

    def listen_once(
        self,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Listen for wake word once.

        Args:
            timeout: Maximum time to wait in seconds

        Returns:
            True if wake word detected, False if timeout
        """
        detected = threading.Event()

        def on_detect():
            detected.set()
            self.stop()

        listen_thread = threading.Thread(
            target=self.listen,
            args=(on_detect,),
            daemon=True
        )
        listen_thread.start()

        result = detected.wait(timeout=timeout)
        self.stop()
        listen_thread.join(timeout=1.0)

        return result

    def stop(self):
        """Stop listening."""
        self._stop_requested = True
        self.is_listening = False


def create_jarvis_model():
    """
    Instructions for creating a custom 'Jarvis' wake word model.

    OpenWakeWord allows training custom models with synthetic speech.
    For now, we'll use the 'alexa' model as fallback.

    To train a custom model:
    1. Generate synthetic "Jarvis" audio clips using TTS
    2. Use OpenWakeWord's training scripts
    3. Place the model in models/hey_jarvis.onnx
    """
    logger.info(
        "Custom 'Jarvis' model not available. "
        "Using 'alexa' or 'hey_mycroft' as fallback. "
        "Say 'Alexa' to activate."
    )
