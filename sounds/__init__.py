"""
JARVIS Sound Effects Module
Provides audio feedback for different states and events.
"""

import subprocess
import shutil
import logging
import os
import math
from pathlib import Path
from typing import Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SoundEvent(Enum):
    """Types of sound events."""
    STARTUP = "startup"
    LISTENING = "listening"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"
    WAKE_DETECTED = "wake_detected"
    NOTIFICATION = "notification"


class SoundManager:
    """Manages sound effects playback."""

    # Frequency definitions for generated tones (Hz)
    TONE_FREQUENCIES = {
        SoundEvent.STARTUP: [(440, 0.1), (554, 0.1), (659, 0.2)],  # A-C#-E arpeggio
        SoundEvent.LISTENING: [(880, 0.15)],  # High A
        SoundEvent.PROCESSING: [(440, 0.1), (440, 0.1)],  # Double beep
        SoundEvent.COMPLETE: [(659, 0.1), (880, 0.15)],  # E-A success
        SoundEvent.ERROR: [(220, 0.3)],  # Low tone
        SoundEvent.WAKE_DETECTED: [(554, 0.1), (659, 0.1)],  # C#-E
        SoundEvent.NOTIFICATION: [(659, 0.15)],  # Single E
    }

    def __init__(self, sounds_dir: Optional[str] = None, enabled: bool = True):
        self.sounds_dir = Path(sounds_dir) if sounds_dir else Path(__file__).parent
        self.enabled = enabled
        self.player = self._detect_player()
        self._volume = 0.5  # 0.0 to 1.0

        logger.info(f"Sound manager initialized, player: {self.player}")

    def _detect_player(self) -> Optional[str]:
        """Detect available audio player."""
        players = ["paplay", "aplay", "ffplay", "play"]
        for player in players:
            if shutil.which(player):
                return player
        return None

    def set_enabled(self, enabled: bool):
        """Enable or disable sounds."""
        self.enabled = enabled

    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        self._volume = max(0.0, min(1.0, volume))

    def play(self, event: SoundEvent):
        """Play a sound for the given event."""
        if not self.enabled:
            return

        # Try to play WAV file first
        wav_file = self.sounds_dir / f"{event.value}.wav"
        if wav_file.exists():
            self._play_file(str(wav_file))
            return

        # Generate and play tone
        self._play_tones(event)

    def _play_file(self, file_path: str):
        """Play a WAV file."""
        if not self.player:
            logger.warning("No audio player available")
            return

        try:
            if self.player == "paplay":
                subprocess.Popen(
                    ["paplay", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif self.player == "aplay":
                subprocess.Popen(
                    ["aplay", "-q", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif self.player == "ffplay":
                subprocess.Popen(
                    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            elif self.player == "play":
                subprocess.Popen(
                    ["play", "-q", file_path],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        except Exception as e:
            logger.error(f"Failed to play sound: {e}")

    def _play_tones(self, event: SoundEvent):
        """Generate and play tones for an event."""
        if not shutil.which("paplay"):
            return

        tones = self.TONE_FREQUENCIES.get(event, [(440, 0.1)])

        for freq, duration in tones:
            self._generate_and_play_tone(freq, duration)

    def _generate_and_play_tone(self, frequency: float, duration: float):
        """Generate and play a simple sine wave tone."""
        try:
            # Use speaker-test for simple beep (most compatible)
            if shutil.which("speaker-test"):
                subprocess.run(
                    ["speaker-test", "-t", "sine", "-f", str(int(frequency)),
                     "-l", "1", "-p", str(int(duration * 1000))],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=duration + 0.5
                )
            # Fallback: use beep if available
            elif shutil.which("beep"):
                subprocess.run(
                    ["beep", "-f", str(int(frequency)), "-l", str(int(duration * 1000))],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=duration + 0.5
                )
        except Exception as e:
            logger.debug(f"Tone generation failed: {e}")

    def play_startup(self):
        """Play startup sound."""
        self.play(SoundEvent.STARTUP)

    def play_listening(self):
        """Play listening indicator."""
        self.play(SoundEvent.LISTENING)

    def play_processing(self):
        """Play processing indicator."""
        self.play(SoundEvent.PROCESSING)

    def play_complete(self):
        """Play completion sound."""
        self.play(SoundEvent.COMPLETE)

    def play_error(self):
        """Play error sound."""
        self.play(SoundEvent.ERROR)

    def play_wake_detected(self):
        """Play wake word detected sound."""
        self.play(SoundEvent.WAKE_DETECTED)

    def play_notification(self):
        """Play notification sound."""
        self.play(SoundEvent.NOTIFICATION)


# Singleton instance
_sound_manager: Optional[SoundManager] = None


def get_sound_manager(sounds_dir: Optional[str] = None,
                      enabled: bool = True) -> SoundManager:
    """Get or create the sound manager instance."""
    global _sound_manager

    if _sound_manager is None:
        _sound_manager = SoundManager(sounds_dir, enabled)

    return _sound_manager
