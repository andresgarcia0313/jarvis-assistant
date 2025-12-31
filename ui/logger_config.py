"""
Configuración centralizada de logging para JARVIS.
Proporciona logs detallados para debugging y monitoreo.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Directorio de logs
LOG_DIR = Path.home() / ".local" / "share" / "jarvis" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Formato detallado para archivo
FILE_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-25s | %(message)s"

# Formato para consola (más compacto)
CONSOLE_FORMAT = "%(asctime)s | %(levelname)-8s | %(message)s"

# Colores para consola
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m'
}


class ColoredFormatter(logging.Formatter):
    """Formatter con colores para la consola."""

    def format(self, record):
        color = COLORS.get(record.levelname, COLORS['RESET'])
        reset = COLORS['RESET']
        record.levelname = f"{color}{record.levelname}{reset}"
        return super().format(record)


class JarvisLogger:
    """Sistema de logging centralizado para JARVIS."""

    _instance: Optional['JarvisLogger'] = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if JarvisLogger._initialized:
            return
        JarvisLogger._initialized = True

        self.log_file = LOG_DIR / f"jarvis_{datetime.now().strftime('%Y%m%d')}.log"
        self._setup_root_logger()
        self._loggers = {}

    def _setup_root_logger(self):
        """Configura el logger raíz."""
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)

        # Handler para archivo (todo nivel DEBUG+)
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(FILE_FORMAT))
        root.addHandler(file_handler)

        # Handler para consola (nivel INFO+)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter(CONSOLE_FORMAT))
        root.addHandler(console_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Obtiene un logger para el módulo especificado."""
        if name not in self._loggers:
            self._loggers[name] = logging.getLogger(name)
        return self._loggers[name]

    def log_event(self, event_type: str, details: dict):
        """Registra un evento estructurado."""
        logger = self.get_logger("events")
        detail_str = " | ".join(f"{k}={v}" for k, v in details.items())
        logger.info(f"[{event_type}] {detail_str}")

    def log_audio(self, action: str, **kwargs):
        """Registra eventos de audio."""
        self.log_event("AUDIO", {"action": action, **kwargs})

    def log_stt(self, action: str, **kwargs):
        """Registra eventos de STT."""
        self.log_event("STT", {"action": action, **kwargs})

    def log_tts(self, action: str, **kwargs):
        """Registra eventos de TTS."""
        self.log_event("TTS", {"action": action, **kwargs})

    def log_brain(self, action: str, **kwargs):
        """Registra eventos del cerebro (Claude)."""
        self.log_event("BRAIN", {"action": action, **kwargs})

    def log_ui(self, action: str, **kwargs):
        """Registra eventos de UI."""
        self.log_event("UI", {"action": action, **kwargs})

    def get_log_path(self) -> Path:
        """Retorna la ruta del archivo de log actual."""
        return self.log_file

    def get_recent_logs(self, lines: int = 50) -> list:
        """Retorna las últimas N líneas del log."""
        if not self.log_file.exists():
            return []
        with open(self.log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]


# Instancia global
_jarvis_logger = JarvisLogger()


def get_logger(name: str) -> logging.Logger:
    """Función helper para obtener logger."""
    return _jarvis_logger.get_logger(name)


def log_event(event_type: str, details: dict):
    """Función helper para registrar eventos."""
    _jarvis_logger.log_event(event_type, details)


def log_audio(action: str, **kwargs):
    _jarvis_logger.log_audio(action, **kwargs)


def log_stt(action: str, **kwargs):
    _jarvis_logger.log_stt(action, **kwargs)


def log_tts(action: str, **kwargs):
    _jarvis_logger.log_tts(action, **kwargs)


def log_brain(action: str, **kwargs):
    _jarvis_logger.log_brain(action, **kwargs)


def log_ui(action: str, **kwargs):
    _jarvis_logger.log_ui(action, **kwargs)


def get_log_path() -> Path:
    return _jarvis_logger.get_log_path()


def get_recent_logs(lines: int = 50) -> list:
    return _jarvis_logger.get_recent_logs(lines)
