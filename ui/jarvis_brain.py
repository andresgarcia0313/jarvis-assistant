"""
Cerebro de JARVIS - Conecta STT con Claude CLI y TTS.
"""

import subprocess
import threading
import logging
import shutil
import os
from typing import Callable, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


def find_claude_cli() -> Optional[str]:
    """Busca el ejecutable de Claude CLI en ubicaciones conocidas."""
    # Primero intentar con which/shutil
    claude_path = shutil.which("claude")
    if claude_path:
        return claude_path

    # Ubicaciones conocidas donde puede estar Claude CLI
    known_paths = [
        Path.home() / ".local" / "bin" / "claude",
        Path.home() / ".npm-global" / "bin" / "claude",
        Path("/usr/local/bin/claude"),
        Path("/usr/bin/claude"),
    ]

    for path in known_paths:
        if path.exists() and os.access(path, os.X_OK):
            logger.info(f"Claude CLI encontrado en: {path}")
            return str(path)

    return None

SYSTEM_PROMPT = """Eres JARVIS, el asistente de inteligencia artificial de Tony Stark.

PERSONALIDAD:
- Elegante, profesional, con sutil humor británico
- Usa "Señor" ocasionalmente, no en cada frase
- Conciso pero completo. Respuestas directas.
- Ligeramente sarcástico ante ideas arriesgadas
- Genuina preocupación por el bienestar del usuario

CAPACIDADES:
- Puedes controlar el sistema (abrir apps, volumen, etc.)
- Tienes acceso a información del sistema
- Puedes ejecutar comandos cuando se te pida

FRASES CARACTERÍSTICAS:
- "A su servicio"
- "Me temo que..."
- "Si me permite sugerir..."
- "Como desee, señor"

Responde siempre en español. Sé útil y eficiente."""


class JarvisBrain:
    """Procesa comandos con Claude CLI."""

    def __init__(self, claude_cmd: Optional[str] = None):
        # Auto-detectar Claude CLI si no se especifica
        if claude_cmd is None:
            self.claude_cmd = find_claude_cli()
            if self.claude_cmd:
                logger.info(f"Usando Claude CLI: {self.claude_cmd}")
            else:
                logger.warning("Claude CLI no encontrado")
        else:
            self.claude_cmd = claude_cmd
        self._processing = False

    def process(
        self,
        text: str,
        on_response: Callable[[str], None],
        on_error: Callable[[str], None]
    ):
        """Procesa texto con Claude en background."""
        if self._processing:
            return

        self._processing = True
        thread = threading.Thread(
            target=self._process_thread,
            args=(text, on_response, on_error),
            daemon=True
        )
        thread.start()

    def _process_thread(
        self,
        text: str,
        on_response: Callable[[str], None],
        on_error: Callable[[str], None]
    ):
        try:
            # Verificar que Claude CLI está disponible
            if not self.claude_cmd:
                on_error("Claude CLI no encontrado. Instalar desde: https://claude.ai/download")
                return

            # Construir prompt con contexto de JARVIS
            full_prompt = f"""[CONTEXTO: {SYSTEM_PROMPT}]

Usuario: {text}

Responde como JARVIS:"""

            result = subprocess.run(
                [self.claude_cmd, "-p", full_prompt, "--output-format", "text"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0 and result.stdout.strip():
                on_response(result.stdout.strip())
            else:
                error = result.stderr.strip() or "Sin respuesta"
                on_error(f"Error: {error}")

        except subprocess.TimeoutExpired:
            on_error("Timeout: Claude tardó demasiado")
        except FileNotFoundError:
            on_error("Claude CLI no encontrado. Instalar desde: https://claude.ai/download")
        except Exception as e:
            on_error(f"Error: {e}")
        finally:
            self._processing = False

    def is_processing(self) -> bool:
        return self._processing
