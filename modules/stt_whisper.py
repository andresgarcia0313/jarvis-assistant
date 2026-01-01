"""
JARVIS Whisper STT Module - High accuracy speech recognition.
Uses faster-whisper for local, offline transcription.
"""
import logging
import numpy as np
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class WhisperSTT:
    """Faster-whisper based speech-to-text with high accuracy."""

    def __init__(
        self,
        model_size: str = "tiny",
        language: str = "es",
        device: str = "cpu",
        compute_type: str = "int8"
    ):
        from faster_whisper import WhisperModel

        self.language = language
        self.sample_rate = 16000

        cache_dir = Path.home() / ".cache" / "whisper"
        cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Loading Whisper model: {model_size}")
        self.model = WhisperModel(
            model_size,
            device=device,
            compute_type=compute_type,
            download_root=str(cache_dir)
        )
        logger.info("Whisper STT initialized")

    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        """
        Transcribe audio array to text.

        Args:
            audio: numpy array (int16 or float32), mono, 16kHz

        Returns:
            Transcribed text or None
        """
        if audio is None or len(audio) == 0:
            return None

        # Convert int16 to float32 normalized
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0

        # Ensure mono
        if len(audio.shape) > 1:
            audio = audio.mean(axis=1)

        try:
            segments, info = self.model.transcribe(
                audio,
                language=self.language,
                beam_size=3,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500}
            )

            text = " ".join(seg.text.strip() for seg in segments)
            return text.strip() if text else None

        except Exception as e:
            logger.error(f"Transcription error: {e}")
            return None

    def transcribe_file(self, path: str) -> Optional[str]:
        """Transcribe audio file."""
        try:
            segments, _ = self.model.transcribe(
                path,
                language=self.language,
                beam_size=3,
                vad_filter=True
            )
            text = " ".join(seg.text.strip() for seg in segments)
            return text.strip() if text else None
        except Exception as e:
            logger.error(f"File transcription error: {e}")
            return None


if __name__ == "__main__":
    import sounddevice as sd

    print("Testing WhisperSTT...")
    stt = WhisperSTT(model_size="tiny", language="es")

    print("Recording 3 seconds... Speak now!")
    audio = sd.rec(3 * 16000, samplerate=16000, channels=1, dtype="int16")
    sd.wait()

    print("Transcribing...")
    result = stt.transcribe(audio.flatten())
    print(f"Result: {result}")
