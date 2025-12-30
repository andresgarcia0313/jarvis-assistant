"""
JARVIS Text-to-Speech Module
Uses Piper for local, offline speech synthesis
"""

import io
import wave
import threading
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import sounddevice as sd

logger = logging.getLogger(__name__)

# Try to import piper, handle if not available
try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False
    logger.warning("Piper not available, TTS will use fallback")


class TextToSpeech:
    """Piper-based text-to-speech engine with interruption support."""

    def __init__(
        self,
        model_path: str,
        config_path: Optional[str] = None,
        speed: float = 1.0,
        speaker_id: int = 0
    ):
        self.speed = speed
        self.speaker_id = speaker_id
        self.is_speaking = False
        self._stop_requested = False
        self._playback_thread: Optional[threading.Thread] = None
        self._stream: Optional[sd.OutputStream] = None

        model_path = Path(model_path)

        if not PIPER_AVAILABLE:
            logger.warning("Piper not installed, using espeak fallback")
            self.voice = None
            self.sample_rate = 22050
            return

        if not model_path.exists():
            raise FileNotFoundError(
                f"Piper model not found at {model_path}. "
                "Run install_phase1.sh to download models."
            )

        # Config path defaults to model path with .json extension
        if config_path is None:
            config_path = str(model_path) + ".json"

        logger.info(f"Loading Piper model from {model_path}")
        self.voice = PiperVoice.load(str(model_path), config_path=config_path)
        self.sample_rate = self.voice.config.sample_rate

        logger.info("TTS module initialized")

    def speak(self, text: str, blocking: bool = True) -> bool:
        """
        Synthesize and play speech.

        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete

        Returns:
            True if completed, False if interrupted
        """
        if not text:
            return True

        self._stop_requested = False

        if blocking:
            return self._speak_blocking(text)
        else:
            self._playback_thread = threading.Thread(
                target=self._speak_blocking,
                args=(text,),
                daemon=True
            )
            self._playback_thread.start()
            return True

    def _speak_blocking(self, text: str) -> bool:
        """Internal blocking speech synthesis."""
        self.is_speaking = True

        try:
            if self.voice is None:
                # Fallback to espeak
                return self._speak_espeak(text)

            # Generate audio with Piper
            audio_data = []
            for audio_chunk in self.voice.synthesize(text):
                if self._stop_requested:
                    logger.debug("Speech interrupted during synthesis")
                    return False
                # AudioChunk has audio_int16_bytes attribute
                audio_data.append(audio_chunk.audio_int16_bytes)

            # Convert to numpy array
            audio_bytes = b''.join(audio_data)
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_float = audio_array.astype(np.float32) / 32768.0

            # Play audio with interruption support
            return self._play_audio(audio_float)

        except Exception as e:
            logger.error(f"Error during speech synthesis: {e}")
            return False
        finally:
            self.is_speaking = False

    def _play_audio(self, audio: np.ndarray) -> bool:
        """Play audio with interruption support."""
        chunk_size = 1024
        position = 0

        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='float32'
            )
            self._stream.start()

            while position < len(audio) and not self._stop_requested:
                end = min(position + chunk_size, len(audio))
                chunk = audio[position:end]
                self._stream.write(chunk)
                position = end

            if not self._stop_requested:
                # Wait for audio to finish
                sd.wait()
                return True
            else:
                logger.debug("Speech interrupted during playback")
                return False

        finally:
            if self._stream:
                self._stream.stop()
                self._stream.close()
                self._stream = None

    def _speak_espeak(self, text: str) -> bool:
        """Fallback using espeak."""
        import subprocess

        try:
            process = subprocess.Popen(
                ['espeak', '-v', 'es', text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            while process.poll() is None:
                if self._stop_requested:
                    process.terminate()
                    return False

            return process.returncode == 0
        except FileNotFoundError:
            logger.error("espeak not found, install with: sudo apt install espeak")
            return False

    def stop(self):
        """Stop speaking immediately."""
        self._stop_requested = True
        if self._stream:
            try:
                self._stream.abort()
            except:
                pass

    def wait(self):
        """Wait for non-blocking speech to complete."""
        if self._playback_thread and self._playback_thread.is_alive():
            self._playback_thread.join()


def download_model(model_name: str, target_dir: str) -> tuple[str, str]:
    """
    Download a Piper model.

    Args:
        model_name: Name of the model (e.g., 'es_ES-davefx-medium')
        target_dir: Directory to save the model

    Returns:
        Tuple of (model_path, config_path)
    """
    import urllib.request

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    model_file = f"{model_name}.onnx"
    config_file = f"{model_name}.onnx.json"

    model_path = target_dir / model_file
    config_path = target_dir / config_file

    if model_path.exists() and config_path.exists():
        logger.info(f"Model already exists at {model_path}")
        return str(model_path), str(config_path)

    # Piper models URL
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main"
    lang = model_name.split("-")[0]  # e.g., 'es_ES'
    lang_short = lang.split("_")[0]  # e.g., 'es'
    voice_name = "-".join(model_name.split("-")[1:-1])  # e.g., 'davefx'
    quality = model_name.split("-")[-1]  # e.g., 'medium'

    model_url = f"{base_url}/{lang_short}/{lang}/{voice_name}/{quality}/{model_file}"
    config_url = f"{base_url}/{lang_short}/{lang}/{voice_name}/{quality}/{config_file}"

    logger.info(f"Downloading Piper model {model_name}...")
    urllib.request.urlretrieve(model_url, model_path)
    urllib.request.urlretrieve(config_url, config_path)

    logger.info(f"Model ready at {model_path}")
    return str(model_path), str(config_path)
