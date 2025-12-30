"""
JARVIS Speech-to-Text Module
Uses Vosk for local, offline speech recognition
"""

import json
import queue
import logging
from pathlib import Path
from typing import Optional, Callable

import sounddevice as sd
import numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel

logger = logging.getLogger(__name__)


class SpeechToText:
    """Vosk-based speech-to-text engine with streaming support."""

    def __init__(
        self,
        model_path: str,
        sample_rate: int = 16000,
        silence_timeout: float = 2.0,
        max_recording_time: float = 30.0
    ):
        self.sample_rate = sample_rate
        self.silence_timeout = silence_timeout
        self.max_recording_time = max_recording_time
        self.audio_queue: queue.Queue = queue.Queue()
        self.is_listening = False
        self._stop_requested = False

        # Suppress Vosk logs
        SetLogLevel(-1)

        # Load model
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Vosk model not found at {model_path}. "
                "Run install_phase1.sh to download models."
            )

        logger.info(f"Loading Vosk model from {model_path}")
        self.model = Model(str(model_path))
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)

        logger.info("STT module initialized")

    def _audio_callback(self, indata, frames, time, status):
        """Callback for audio stream."""
        if status:
            logger.warning(f"Audio status: {status}")
        self.audio_queue.put(bytes(indata))

    def listen(
        self,
        on_partial: Optional[Callable[[str], None]] = None,
        interrupt_check: Optional[Callable[[], bool]] = None
    ) -> Optional[str]:
        """
        Listen and transcribe speech.

        Args:
            on_partial: Callback for partial results (real-time feedback)
            interrupt_check: Function that returns True to stop listening

        Returns:
            Transcribed text or None if interrupted/timeout
        """
        self.is_listening = True
        self._stop_requested = False
        self.audio_queue = queue.Queue()

        silence_frames = 0
        max_silence_frames = int(self.silence_timeout * self.sample_rate / 1024)
        max_frames = int(self.max_recording_time * self.sample_rate / 1024)
        frame_count = 0

        final_text = ""
        has_speech = False

        try:
            with sd.RawInputStream(
                samplerate=self.sample_rate,
                blocksize=1024,
                dtype='int16',
                channels=1,
                callback=self._audio_callback
            ):
                logger.debug("Started listening...")

                while self.is_listening and not self._stop_requested:
                    # Check for interrupt
                    if interrupt_check and interrupt_check():
                        logger.debug("Listening interrupted by external signal")
                        break

                    # Check timeout
                    frame_count += 1
                    if frame_count >= max_frames:
                        logger.debug("Max recording time reached")
                        break

                    try:
                        data = self.audio_queue.get(timeout=0.1)
                    except queue.Empty:
                        continue

                    # Process audio
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").strip()
                        if text:
                            final_text = text
                            has_speech = True
                            logger.debug(f"Final result: {text}")
                    else:
                        partial = json.loads(self.recognizer.PartialResult())
                        partial_text = partial.get("partial", "").strip()

                        if partial_text:
                            has_speech = True
                            silence_frames = 0
                            if on_partial:
                                on_partial(partial_text)
                        elif has_speech:
                            silence_frames += 1
                            if silence_frames >= max_silence_frames:
                                logger.debug("Silence timeout reached")
                                break

                # Get final result
                final_result = json.loads(self.recognizer.FinalResult())
                if final_result.get("text", "").strip():
                    final_text = final_result["text"].strip()

        except Exception as e:
            logger.error(f"Error during speech recognition: {e}")
            return None
        finally:
            self.is_listening = False

        logger.info(f"Transcribed: {final_text}")
        return final_text if final_text else None

    def stop(self):
        """Stop listening."""
        self._stop_requested = True
        self.is_listening = False


def download_model(model_name: str, target_dir: str) -> str:
    """
    Download a Vosk model.

    Args:
        model_name: Name of the model (e.g., 'vosk-model-small-es-0.42')
        target_dir: Directory to save the model

    Returns:
        Path to the downloaded model
    """
    import urllib.request
    import zipfile
    import os

    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    model_path = target_dir / model_name
    if model_path.exists():
        logger.info(f"Model already exists at {model_path}")
        return str(model_path)

    url = f"https://alphacephei.com/vosk/models/{model_name}.zip"
    zip_path = target_dir / f"{model_name}.zip"

    logger.info(f"Downloading {model_name}...")
    urllib.request.urlretrieve(url, zip_path)

    logger.info(f"Extracting {model_name}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(target_dir)

    zip_path.unlink()
    logger.info(f"Model ready at {model_path}")

    return str(model_path)
