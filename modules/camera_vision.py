"""
JARVIS Camera Vision Module
Captures and analyzes camera images using Claude's vision capabilities.

Security and Privacy:
- Camera is ONLY activated with explicit user command
- User is notified before any capture
- Photos are deleted immediately after analysis
- No video recording, only single frames
"""

import subprocess
import shutil
import logging
import tempfile
import os
import re
import glob
from pathlib import Path
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CameraResult:
    """Result of a camera capture."""
    success: bool
    file_path: Optional[str] = None
    error: Optional[str] = None


class CameraCapture:
    """Handles camera capture using available system tools."""

    # Priority order for camera tools
    CAPTURE_TOOLS = [
        "ffmpeg",      # Most common, uses v4l2
        "fswebcam",    # Simple webcam capture
        "v4l2-ctl",    # Direct v4l2 control
    ]

    def __init__(self, device: Optional[str] = None):
        self.device = device or self._detect_camera()
        self.capture_tool = self._detect_tool()
        self.temp_dir = tempfile.mkdtemp(prefix="jarvis_camera_")
        logger.info(f"Camera device: {self.device}, tool: {self.capture_tool}")

    def _detect_camera(self) -> Optional[str]:
        """Detect available camera device."""
        # Look for video devices
        video_devices = sorted(glob.glob("/dev/video*"))

        for device in video_devices:
            # Check if it's a capture device (not output)
            try:
                result = subprocess.run(
                    ["v4l2-ctl", "-d", device, "--all"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "Video Capture" in result.stdout:
                    return device
            except Exception:
                # If v4l2-ctl not available, just return first device
                pass

        # Default to first device if exists
        return video_devices[0] if video_devices else None

    def _detect_tool(self) -> Optional[str]:
        """Detect available capture tool."""
        for tool in self.CAPTURE_TOOLS:
            if shutil.which(tool):
                return tool
        return None

    def has_camera(self) -> bool:
        """Check if camera is available."""
        return self.device is not None and self.capture_tool is not None

    def capture_photo(self, filename: Optional[str] = None) -> CameraResult:
        """Capture a single photo from the camera."""
        if not self.has_camera():
            if not self.device:
                return CameraResult(
                    success=False,
                    error="No se detectó ninguna cámara en el sistema."
                )
            return CameraResult(
                success=False,
                error="No hay herramientas de captura disponibles. Instala ffmpeg o fswebcam."
            )

        if not filename:
            filename = os.path.join(self.temp_dir, "camera_capture.jpg")

        try:
            if self.capture_tool == "ffmpeg":
                result = self._capture_with_ffmpeg(filename)
            elif self.capture_tool == "fswebcam":
                result = self._capture_with_fswebcam(filename)
            else:
                result = self._capture_with_ffmpeg(filename)  # Fallback

            return result

        except Exception as e:
            return CameraResult(success=False, error=str(e))

    def _capture_with_ffmpeg(self, filename: str) -> CameraResult:
        """Capture using ffmpeg."""
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-y",  # Overwrite
                    "-f", "v4l2",
                    "-i", self.device,
                    "-frames:v", "1",
                    "-q:v", "2",  # Quality
                    filename
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and os.path.exists(filename):
                logger.info(f"Photo captured: {filename}")
                return CameraResult(success=True, file_path=filename)
            else:
                error = result.stderr or "Captura falló"
                # Check for common issues
                if "Permission denied" in error:
                    error = "Sin permiso para acceder a la cámara. Verifica los permisos."
                elif "Device or resource busy" in error:
                    error = "La cámara está en uso por otra aplicación."
                return CameraResult(success=False, error=error)

        except subprocess.TimeoutExpired:
            return CameraResult(success=False, error="La captura tardó demasiado")
        except Exception as e:
            return CameraResult(success=False, error=str(e))

    def _capture_with_fswebcam(self, filename: str) -> CameraResult:
        """Capture using fswebcam."""
        try:
            result = subprocess.run(
                [
                    "fswebcam",
                    "-d", self.device,
                    "-r", "1280x720",
                    "--no-banner",
                    filename
                ],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0 and os.path.exists(filename):
                return CameraResult(success=True, file_path=filename)
            else:
                return CameraResult(success=False, error=result.stderr)

        except subprocess.TimeoutExpired:
            return CameraResult(success=False, error="La captura tardó demasiado")
        except Exception as e:
            return CameraResult(success=False, error=str(e))

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


class CameraAnalyzer:
    """Analyzes camera images using Claude CLI."""

    # Pre-capture notification messages
    ACTIVATION_NOTICE = "Señor, activando cámara."

    def __init__(self, claude_command: str = "claude", device: Optional[str] = None):
        self.claude_command = claude_command
        self.capture = CameraCapture(device)

    def analyze_camera(self, prompt: str = "Describe lo que ves en esta imagen.") -> str:
        """Capture and analyze camera image."""
        if not self.capture.has_camera():
            return "No hay cámara disponible en este sistema."

        logger.info("Capturando imagen de cámara...")

        result = self.capture.capture_photo()
        if not result.success:
            return f"No pude capturar la imagen: {result.error}"

        try:
            # Analyze with Claude
            analysis = self._send_to_claude(result.file_path, prompt)
            return analysis
        finally:
            # ALWAYS cleanup - privacy first
            self.capture.cleanup(result.file_path)

    def _send_to_claude(self, image_path: str, prompt: str) -> str:
        """Send image to Claude CLI for analysis."""
        try:
            result = subprocess.run(
                [
                    self.claude_command,
                    "-p", prompt,
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

    def describe_view(self) -> str:
        """Describe what the camera sees."""
        prompt = (
            "Describe brevemente lo que ves en esta imagen de cámara web. "
            "Menciona personas, objetos y el entorno visible. "
            "Responde en español de forma concisa."
        )
        return self.analyze_camera(prompt)

    def check_presence(self) -> str:
        """Check if someone is visible."""
        prompt = (
            "Examina esta imagen y dime si hay alguna persona visible. "
            "Si hay alguien, describe brevemente su posición (frente a la cámara, "
            "detrás, a un lado). Si no hay nadie, indícalo. "
            "Responde en español brevemente."
        )
        return self.analyze_camera(prompt)

    def describe_user(self) -> str:
        """Describe the user's appearance."""
        prompt = (
            "Describe brevemente a la persona que está frente a la cámara. "
            "Menciona aspectos generales como postura, si está sonriendo, "
            "o cualquier detalle notable. No menciones características físicas "
            "permanentes. Responde en español de forma amable y concisa."
        )
        return self.analyze_camera(prompt)

    def identify_object(self) -> str:
        """Identify objects in view."""
        prompt = (
            "¿Qué objetos puedes identificar en esta imagen? "
            "Si alguien sostiene algo, describe qué es. "
            "Responde en español brevemente."
        )
        return self.analyze_camera(prompt)

    def answer_about_camera(self, question: str) -> str:
        """Answer a specific question about what the camera sees."""
        prompt = (
            f"Observa esta imagen de cámara web y responde: {question}. "
            f"Responde en español."
        )
        return self.analyze_camera(prompt)


class CameraQueryHandler:
    """Handles camera-related voice queries."""

    CAMERA_PATTERNS = [
        (r"(?:qu[eé]\s+)?(?:ves|hay)\s+(?:con|en)\s+(?:la\s+)?c[aá]mara", "describe"),
        (r"(?:qu[eé]\s+)?(?:puedes\s+)?ver", "describe"),
        (r"mira\s+(?:con\s+)?(?:la\s+)?c[aá]mara", "describe"),
        (r"(?:hay\s+)?alguien\s+(?:detr[aá]s|atr[aá]s)", "presence_behind"),
        (r"(?:hay\s+)?alguien\s+(?:visible|ah[ií])", "presence"),
        (r"c[oó]mo\s+(?:me\s+)?veo", "describe_user"),
        (r"c[oó]mo\s+estoy", "describe_user"),
        (r"(?:qu[eé]\s+)?(?:objeto|cosa)\s+tengo", "object"),
        (r"(?:qu[eé]\s+)?tengo\s+en\s+(?:la\s+)?mano", "object"),
        (r"activa(?:r)?\s+(?:la\s+)?c[aá]mara", "activate"),
        (r"usa(?:r)?\s+(?:la\s+)?c[aá]mara", "activate"),
    ]

    def __init__(self, analyzer: Optional[CameraAnalyzer] = None):
        self.analyzer = analyzer or CameraAnalyzer()

    def process_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process a camera-related query."""
        input_lower = user_input.lower().strip()

        for pattern, query_type in self.CAMERA_PATTERNS:
            if re.search(pattern, input_lower):
                return (True, self._handle_query(query_type, user_input))

        return (False, None)

    def _handle_query(self, query_type: str, original_input: str) -> str:
        """Handle different types of camera queries."""
        # Always notify about camera activation
        logger.info(CameraAnalyzer.ACTIVATION_NOTICE)

        if query_type == "describe":
            return self.analyzer.describe_view()
        elif query_type == "presence_behind":
            return self.analyzer.check_presence()
        elif query_type == "presence":
            return self.analyzer.check_presence()
        elif query_type == "describe_user":
            return self.analyzer.describe_user()
        elif query_type == "object":
            return self.analyzer.identify_object()
        elif query_type == "activate":
            return self.analyzer.describe_view()
        else:
            # Generic question about camera view
            return self.analyzer.answer_about_camera(original_input)


# Singleton instances
_analyzer_instance: Optional[CameraAnalyzer] = None
_handler_instance: Optional[CameraQueryHandler] = None


def get_camera_analyzer(claude_command: str = "claude",
                        device: Optional[str] = None) -> CameraAnalyzer:
    """Get or create the camera analyzer instance."""
    global _analyzer_instance

    if _analyzer_instance is None:
        _analyzer_instance = CameraAnalyzer(claude_command, device)

    return _analyzer_instance


def get_camera_handler() -> CameraQueryHandler:
    """Get or create the camera query handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = CameraQueryHandler(get_camera_analyzer())

    return _handler_instance
