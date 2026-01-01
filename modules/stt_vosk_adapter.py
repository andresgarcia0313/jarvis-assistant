"""
Vosk STT Adapter - Wraps Vosk to match WhisperSTT interface.
"""
import json
import logging
from typing import Optional
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)


class VoskAdapter:
    """Vosk adapter with transcribe(audio) interface."""

    def __init__(self, model_path: str, language: str = "es"):
        from vosk import Model, KaldiRecognizer, SetLogLevel

        SetLogLevel(-1)  # Suppress Vosk logs
        self.sample_rate = 16000
        self.language = language

        path = Path(model_path)
        if not path.exists():
            raise FileNotFoundError(f"Vosk model not found: {model_path}")

        logger.info(f"Loading Vosk model: {model_path}")
        self.model = Model(str(path))
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        self.recognizer.SetWords(True)
        logger.info("Vosk STT initialized")

    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        """
        Transcribe audio array to text.

        Args:
            audio: numpy array (int16), mono, 16kHz

        Returns:
            Transcribed text or None
        """
        if audio is None or len(audio) == 0:
            return None

        # Ensure int16
        if audio.dtype != np.int16:
            if audio.dtype == np.float32:
                audio = (audio * 32768).astype(np.int16)
            else:
                audio = audio.astype(np.int16)

        # Ensure mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1).astype(np.int16)

        try:
            # Reset recognizer for clean state
            self.recognizer = type(self.recognizer)(self.model, self.sample_rate)
            self.recognizer.SetWords(True)

            # Process audio in chunks
            chunk_size = 4000
            for i in range(0, len(audio), chunk_size):
                chunk = audio[i:i + chunk_size]
                self.recognizer.AcceptWaveform(chunk.tobytes())

            # Get final result
            result = json.loads(self.recognizer.FinalResult())
            text = result.get("text", "").strip()
            return text if text else None

        except Exception as e:
            logger.error(f"Vosk transcription error: {e}")
            return None


if __name__ == "__main__":
    import sounddevice as sd

    MODEL_PATH = "models/vosk-model-small-es-0.42"

    print("Testing VoskAdapter...")
    stt = VoskAdapter(model_path=MODEL_PATH)

    print("Recording 3 seconds... Speak now!")
    audio = sd.rec(3 * 16000, samplerate=16000, channels=1, dtype="int16")
    sd.wait()

    print("Transcribing...")
    result = stt.transcribe(audio.flatten())
    print(f"Result: {result}")
