"""
STT Factory - Creates the appropriate STT engine based on configuration.
Supports: whisper (faster-whisper), vosk
"""
import logging
from typing import Optional, Protocol, Union
import numpy as np

logger = logging.getLogger(__name__)


class STTEngine(Protocol):
    """Protocol for STT engines."""

    def transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Transcribe audio to text."""
        ...


def create_stt(
    engine: str = "whisper",
    model_path: Optional[str] = None,
    language: str = "es",
    **kwargs
) -> STTEngine:
    """
    Create an STT engine instance.

    Args:
        engine: "whisper" or "vosk"
        model_path: Path to model (required for vosk)
        language: Language code (default: "es")
        **kwargs: Additional engine-specific options

    Returns:
        STT engine instance
    """
    if engine == "whisper":
        from modules.stt_whisper import WhisperSTT

        model_size = kwargs.get("model_size", "tiny")
        device = kwargs.get("device", "cpu")
        compute_type = kwargs.get("compute_type", "int8")

        logger.info(f"Creating Whisper STT (model={model_size})")
        return WhisperSTT(
            model_size=model_size,
            language=language,
            device=device,
            compute_type=compute_type
        )

    elif engine == "vosk":
        from modules.stt_vosk_adapter import VoskAdapter

        if not model_path:
            raise ValueError("model_path required for Vosk engine")

        logger.info(f"Creating Vosk STT (model={model_path})")
        return VoskAdapter(model_path=model_path, language=language)

    else:
        raise ValueError(f"Unknown STT engine: {engine}. Use 'whisper' or 'vosk'")


if __name__ == "__main__":
    print("Testing STT Factory...")

    # Test Whisper
    stt = create_stt(engine="whisper", language="es", model_size="tiny")
    print(f"Created: {type(stt).__name__}")

    # Quick audio test
    import sounddevice as sd
    print("Recording 3s... Speak!")
    audio = sd.rec(3 * 16000, samplerate=16000, channels=1, dtype="int16")
    sd.wait()

    result = stt.transcribe(audio.flatten())
    print(f"Result: {result}")
