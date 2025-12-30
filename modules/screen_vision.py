"""
JARVIS Screen Vision Module
Captures and analyzes screen content using Claude's vision capabilities.
"""

import subprocess
import shutil
import logging
import tempfile
import os
import re
import base64
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CaptureResult:
    """Result of a screen capture."""
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None


class ScreenCapture:
    """Handles screen capture using available system tools."""

    # Priority order for screenshot tools
    CAPTURE_TOOLS = [
        ("spectacle", ["-b", "-n", "-o"]),  # KDE: background, no notify, output
        ("scrot", ["-o"]),  # scrot: overwrite
        ("gnome-screenshot", ["-f"]),  # GNOME: file
        ("import", ["-window", "root"]),  # ImageMagick
    ]

    def __init__(self):
        self.capture_tool = self._detect_tool()
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_screen_")
        logger.info(f"Screen capture tool: {self.capture_tool or 'none'}")

    def _detect_tool(self) -> Optional[str]:
        """Detect available screenshot tool."""
        for tool, _ in self.CAPTURE_TOOLS:
            if shutil.which(tool):
                return tool
        return None

    def capture_screen(self, filename: Optional[str] = None) -> CaptureResult:
        """Capture the full screen."""
        if not self.capture_tool:
            return CaptureResult(
                success=False,
                error="No hay herramientas de captura disponibles. Instala spectacle o scrot."
            )

        if not filename:
            filename = os.path.join(self.temp_dir, "screen_capture.png")

        try:
            # Get command args for the detected tool
            args = self._get_capture_args(filename)

            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and os.path.exists(filename):
                logger.info(f"Screen captured: {filename}")
                return CaptureResult(success=True, file_path=filename)
            else:
                error = result.stderr or "Captura falló sin mensaje de error"
                return CaptureResult(success=False, error=error)

        except subprocess.TimeoutExpired:
            return CaptureResult(success=False, error="La captura tardó demasiado")
        except Exception as e:
            return CaptureResult(success=False, error=str(e))

    def _get_capture_args(self, filename: str) -> list:
        """Get command arguments for the capture tool."""
        for tool, args in self.CAPTURE_TOOLS:
            if tool == self.capture_tool:
                if tool == "spectacle":
                    return [tool] + args + [filename]
                elif tool == "scrot":
                    return [tool] + args + [filename]
                elif tool == "gnome-screenshot":
                    return [tool] + args + [filename]
                elif tool == "import":
                    return [tool] + args + [filename]
        return [self.capture_tool, filename]

    def capture_region(self, x: int, y: int, width: int, height: int,
                       filename: Optional[str] = None) -> CaptureResult:
        """Capture a specific region of the screen."""
        if not self.capture_tool:
            return CaptureResult(
                success=False,
                error="No hay herramientas de captura disponibles."
            )

        if not filename:
            filename = os.path.join(self.temp_dir, "region_capture.png")

        try:
            if self.capture_tool == "import":
                # ImageMagick import with geometry
                geometry = f"{width}x{height}+{x}+{y}"
                result = subprocess.run(
                    ["import", "-window", "root", "-crop", geometry, filename],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            elif self.capture_tool == "spectacle":
                # Spectacle with region (requires interactive, fall back to full)
                return self.capture_screen(filename)
            else:
                # Fall back to full screen for other tools
                return self.capture_screen(filename)

            if result.returncode == 0 and os.path.exists(filename):
                return CaptureResult(success=True, file_path=filename)
            else:
                return CaptureResult(success=False, error=result.stderr)

        except Exception as e:
            return CaptureResult(success=False, error=str(e))

    def cleanup(self, file_path: Optional[str] = None):
        """Remove captured files."""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Removed capture: {file_path}")
            elif os.path.exists(self.temp_dir):
                for f in os.listdir(self.temp_dir):
                    os.remove(os.path.join(self.temp_dir, f))
        except Exception as e:
            logger.warning(f"Failed to cleanup: {e}")

    def __del__(self):
        """Cleanup temp directory on destruction."""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception:
            pass


class ScreenAnalyzer:
    """Analyzes screen content using Claude CLI."""

    def __init__(self, claude_command: str = "claude"):
        self.claude_command = claude_command
        self.capture = ScreenCapture()

    def analyze_screen(self, prompt: str = "Describe lo que ves en esta captura de pantalla.") -> str:
        """Capture and analyze the screen."""
        # Inform about capture
        logger.info("Capturando pantalla...")

        result = self.capture.capture_screen()
        if not result.success:
            return f"No pude capturar la pantalla: {result.error}"

        try:
            # Analyze with Claude
            analysis = self._send_to_claude(result.file_path, prompt)
            return analysis
        finally:
            # Always cleanup
            self.capture.cleanup(result.file_path)

    def _send_to_claude(self, image_path: str, prompt: str) -> str:
        """Send image to Claude CLI for analysis."""
        try:
            # Claude CLI can accept images directly
            result = subprocess.run(
                [
                    self.claude_command,
                    "-p", f"{prompt}",
                    image_path
                ],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"Claude analysis failed: {result.stderr}")
                return "No pude analizar la imagen."

        except subprocess.TimeoutExpired:
            return "El análisis tardó demasiado."
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return f"Error al analizar: {e}"

    def read_screen_text(self) -> str:
        """Read text visible on screen."""
        prompt = (
            "Lee y transcribe TODO el texto visible en esta captura de pantalla. "
            "Incluye texto de ventanas, barras, menús y cualquier texto legible. "
            "Responde en español."
        )
        return self.analyze_screen(prompt)

    def describe_screen(self) -> str:
        """Describe what's on screen."""
        prompt = (
            "Describe brevemente qué hay en esta captura de pantalla. "
            "Menciona las aplicaciones visibles, ventanas abiertas y el contenido principal. "
            "Responde en español de forma concisa."
        )
        return self.analyze_screen(prompt)

    def check_for_errors(self) -> str:
        """Check for error messages on screen."""
        prompt = (
            "Examina esta captura de pantalla buscando mensajes de error, "
            "alertas, advertencias o problemas visibles. "
            "Si hay errores, descríbelos. Si no hay errores, indica que la pantalla "
            "se ve normal. Responde en español."
        )
        return self.analyze_screen(prompt)

    def identify_active_app(self) -> str:
        """Identify the active application."""
        prompt = (
            "Identifica qué aplicación está activa o en primer plano en esta captura. "
            "Menciona el nombre de la aplicación y qué parece estar haciendo el usuario. "
            "Responde en español brevemente."
        )
        return self.analyze_screen(prompt)

    def answer_about_screen(self, question: str) -> str:
        """Answer a specific question about the screen."""
        prompt = (
            f"Observa esta captura de pantalla y responde la siguiente pregunta: {question}. "
            f"Responde en español."
        )
        return self.analyze_screen(prompt)


class ScreenQueryHandler:
    """Handles screen-related voice queries."""

    SCREEN_PATTERNS = [
        (r"(?:qu[eé]\s+)?(?:hay\s+)?en\s+(?:mi\s+)?pantalla", "describe"),
        (r"(?:qu[eé]\s+)?(?:ves|hay)\s+en\s+pantalla", "describe"),
        (r"describe\s+(?:la\s+)?pantalla", "describe"),
        (r"lee\s+(?:el\s+)?texto\s+(?:de\s+)?(?:la\s+)?pantalla", "read_text"),
        (r"(?:qu[eé]\s+)?texto\s+(?:hay\s+)?en\s+pantalla", "read_text"),
        (r"(?:qu[eé]\s+)?aplicaci[oó]n\s+tengo\s+(?:abierta)?", "active_app"),
        (r"(?:qu[eé]\s+)?(?:programa|app)\s+(?:est[aá]\s+)?abierto", "active_app"),
        (r"(?:qu[eé]\s+)?(?:programa|app)\s+tengo\s+abiert[ao]", "active_app"),
        (r"(?:hay\s+)?(?:alg[uú]n\s+)?error(?:es)?\s+(?:visible|en\s+pantalla)?", "errors"),
        (r"(?:qu[eé]\s+)?errores\s+(?:hay\s+)?(?:en\s+pantalla)?", "errors"),
        (r"captura\s+(?:la\s+)?pantalla", "capture_only"),
        (r"screenshot", "capture_only"),
    ]

    def __init__(self, analyzer: Optional[ScreenAnalyzer] = None):
        self.analyzer = analyzer or ScreenAnalyzer()

    def process_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process a screen-related query."""
        input_lower = user_input.lower().strip()

        for pattern, query_type in self.SCREEN_PATTERNS:
            if re.search(pattern, input_lower):
                return (True, self._handle_query(query_type, user_input))

        return (False, None)

    def _handle_query(self, query_type: str, original_input: str) -> str:
        """Handle different types of screen queries."""
        # Notify about capture
        notification = "Capturando pantalla..."
        logger.info(notification)

        if query_type == "describe":
            return self.analyzer.describe_screen()
        elif query_type == "read_text":
            return self.analyzer.read_screen_text()
        elif query_type == "active_app":
            return self.analyzer.identify_active_app()
        elif query_type == "errors":
            return self.analyzer.check_for_errors()
        elif query_type == "capture_only":
            result = self.analyzer.capture.capture_screen()
            if result.success:
                # For capture-only, analyze briefly and cleanup
                analysis = self.analyzer.describe_screen()
                return f"Captura realizada. {analysis}"
            return f"No pude capturar: {result.error}"
        else:
            # Generic question about screen
            return self.analyzer.answer_about_screen(original_input)


# Singleton instances
_analyzer_instance: Optional[ScreenAnalyzer] = None
_handler_instance: Optional[ScreenQueryHandler] = None


def get_screen_analyzer(claude_command: str = "claude") -> ScreenAnalyzer:
    """Get or create the screen analyzer instance."""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = ScreenAnalyzer(claude_command)

    return _analyzer_instance


def get_screen_handler() -> ScreenQueryHandler:
    """Get or create the screen query handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = ScreenQueryHandler(get_screen_analyzer())

    return _handler_instance
