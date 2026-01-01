"""
Whisper Live Listener - Accumulates audio and transcribes in batches.
Optimized for accuracy over real-time streaming.
"""
import queue
import threading
import logging
import time
import numpy as np
import sounddevice as sd
from typing import Callable, Optional

from modules.stt_whisper import WhisperSTT
from ui.vad_detector import VADDetector

logger = logging.getLogger(__name__)


class WhisperLiveListener:
    """Accumulates speech audio and transcribes with Whisper."""

    SILENCE_TIMEOUT = 1.0  # Seconds of silence to trigger transcription
    MAX_AUDIO_DURATION = 15.0  # Max seconds to accumulate

    def __init__(self, sample_rate: int = 16000, device: Optional[int] = None):
        self.sample_rate = sample_rate
        self.device = device
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._audio_level = 0

        # Whisper STT
        self.stt = WhisperSTT(model_size="tiny", language="es")

        # VAD
        self.vad = VADDetector(sample_rate, aggressiveness=2)

        # Audio buffer
        self._audio_buffer: list[np.ndarray] = []
        self._last_speech_time = 0.0
        self._is_recording = False

    def start(self, on_text: Callable[[str, bool], None]):
        """Start continuous listening."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(
            target=self._listen_loop, args=(on_text,), daemon=True
        )
        self._thread.start()

    def _listen_loop(self, on_text: Callable[[str, bool], None]):
        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=2048,
                dtype="int16",
                channels=1,
                device=self.device,
            ) as stream:
                while self.running:
                    audio, _ = stream.read(2048)
                    audio = audio.flatten().astype(np.int16)

                    # Calculate audio level
                    rms = np.sqrt(np.mean(audio.astype(np.float32) ** 2))
                    self._audio_level = min(100, int(rms / 300 * 100))

                    # Detect speech
                    is_speech = self.vad.is_speech(audio.tobytes())
                    now = time.time()

                    if is_speech:
                        self._audio_buffer.append(audio)
                        self._last_speech_time = now
                        self._is_recording = True
                        on_text("...", False)  # Indicate listening

                    elif self._is_recording:
                        # Check silence timeout
                        silence = now - self._last_speech_time
                        buffer_duration = len(self._audio_buffer) * 2048 / self.sample_rate

                        if silence >= self.SILENCE_TIMEOUT or buffer_duration >= self.MAX_AUDIO_DURATION:
                            self._transcribe_buffer(on_text)

        except Exception as e:
            logger.error(f"Listener error: {e}")
        finally:
            self.running = False

    def _transcribe_buffer(self, on_text: Callable[[str, bool], None]):
        """Transcribe accumulated audio."""
        if not self._audio_buffer:
            return

        audio = np.concatenate(self._audio_buffer)
        self._audio_buffer.clear()
        self._is_recording = False

        text = self.stt.transcribe(audio)
        if text:
            on_text(text, True)

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def is_running(self) -> bool:
        return self.running

    def get_audio_level(self) -> int:
        return self._audio_level

    def set_device(self, device_index: Optional[int]):
        """Change audio device (requires restart)."""
        self.device = device_index


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    def on_text(text: str, is_final: bool):
        prefix = "[FINAL]" if is_final else "[...]"
        print(f"{prefix} {text}")

    print("Starting WhisperLiveListener... Speak!")
    listener = WhisperLiveListener()
    listener.start(on_text)

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        listener.stop()
        print("Stopped.")
