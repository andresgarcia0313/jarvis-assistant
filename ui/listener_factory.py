"""
Listener Factory - Creates the appropriate listener based on configuration.
"""
import logging
from typing import Optional, Protocol, Callable

logger = logging.getLogger(__name__)


class Listener(Protocol):
    """Protocol for audio listeners."""

    def start(self, on_text: Callable[[str, bool], None]) -> None: ...
    def stop(self) -> None: ...
    def get_audio_level(self) -> int: ...


def create_listener(
    engine: str = "whisper",
    model_path: Optional[str] = None,
    sample_rate: int = 16000,
    device: Optional[int] = None,
    **kwargs
) -> Listener:
    """
    Create a listener instance based on engine type.

    Args:
        engine: "whisper" or "vosk"
        model_path: Path to Vosk model (required for vosk)
        sample_rate: Audio sample rate
        device: Audio device index
        **kwargs: Additional engine-specific options

    Returns:
        Listener instance
    """
    if engine == "whisper":
        from ui.listener_whisper import WhisperLiveListener

        logger.info("Creating Whisper listener")
        return WhisperLiveListener(sample_rate=sample_rate, device=device)

    elif engine == "vosk":
        from ui.live_listener import LiveListener

        if not model_path:
            raise ValueError("model_path required for Vosk listener")

        logger.info(f"Creating Vosk listener (model={model_path})")
        return LiveListener(
            model_path=model_path,
            sample_rate=sample_rate,
            device=device
        )

    else:
        raise ValueError(f"Unknown engine: {engine}. Use 'whisper' or 'vosk'")


def create_listener_from_config(config: dict, device: Optional[int] = None) -> Listener:
    """Create listener from config.yaml stt section."""
    stt_config = config.get("stt", {})
    engine = stt_config.get("engine", "whisper")
    sample_rate = config.get("audio", {}).get("sample_rate", 16000)

    if engine == "vosk":
        vosk_config = stt_config.get("vosk", {})
        model_path = vosk_config.get("model_path", "models/vosk-model-small-es-0.42")
        return create_listener("vosk", model_path=model_path, sample_rate=sample_rate, device=device)

    return create_listener("whisper", sample_rate=sample_rate, device=device)


if __name__ == "__main__":
    import time
    logging.basicConfig(level=logging.INFO)

    def on_text(text: str, is_final: bool):
        prefix = "[FINAL]" if is_final else "[...]"
        print(f"{prefix} {text}")

    # Test Whisper listener
    listener = create_listener("whisper")
    print("Starting listener... Speak!")
    listener.start(on_text)

    try:
        for _ in range(100):  # 10 seconds
            print(f"Level: {listener.get_audio_level()}", end="\r")
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        listener.stop()
        print("\nStopped.")
