"""
JARVIS System Control Module
Handles system actions: open/close apps, volume, brightness, terminal commands.
Implements safety checks and action logging.
"""

import subprocess
import shutil
import logging
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ActionRisk(Enum):
    """Risk levels for system actions."""
    SAFE = "safe"           # No confirmation needed
    MODERATE = "moderate"   # Log but no confirmation
    DANGEROUS = "dangerous" # Requires confirmation
    FORBIDDEN = "forbidden" # Never execute


@dataclass
class ActionResult:
    """Result of a system action."""
    success: bool
    message: str
    action_type: str
    details: Optional[str] = None
    required_confirmation: bool = False


@dataclass
class ActionLog:
    """Log entry for an action."""
    timestamp: datetime
    action_type: str
    command: str
    success: bool
    details: str
    risk_level: ActionRisk


class SystemControl:
    """Controls system actions with safety checks."""

    # Common applications mapping (Spanish -> command)
    APP_ALIASES = {
        # Browsers
        "firefox": ["firefox"],
        "navegador": ["firefox", "chromium", "google-chrome"],
        "chrome": ["google-chrome", "chromium"],
        "chromium": ["chromium"],
        # File managers
        "archivos": ["dolphin", "nautilus", "thunar"],
        "dolphin": ["dolphin"],
        "explorador": ["dolphin", "nautilus"],
        # Terminals
        "terminal": ["konsole", "gnome-terminal", "xterm"],
        "konsole": ["konsole"],
        # Editors
        "editor": ["kate", "gedit", "code"],
        "kate": ["kate"],
        "code": ["code", "codium"],
        "vscode": ["code", "codium"],
        # Media
        "música": ["spotify", "rhythmbox", "vlc"],
        "spotify": ["spotify"],
        "vlc": ["vlc"],
        "reproductor": ["vlc", "totem", "dragon"],
        # Office
        "writer": ["libreoffice --writer"],
        "calc": ["libreoffice --calc"],
        "libreoffice": ["libreoffice"],
        # System
        "configuración": ["systemsettings5", "gnome-control-center"],
        "settings": ["systemsettings5"],
        # Communication
        "slack": ["slack"],
        "discord": ["discord"],
        "telegram": ["telegram-desktop"],
    }

    # Dangerous command patterns
    DANGEROUS_PATTERNS = [
        r"\brm\b.*-rf",
        r"\brm\b.*-fr",
        r"\brmdir\b",
        r"\bmkfs\b",
        r"\bdd\b.*if=",
        r"\b>\s*/dev/",
        r"\bshutdown\b",
        r"\breboot\b",
        r"\bpoweroff\b",
        r"\bkill\b.*-9",
        r"\bkillall\b",
        r"\bsudo\b",
        r"\bchmod\b.*777",
        r"\bchown\b",
        r":(){.*};:",  # Fork bomb
    ]

    # Forbidden patterns (never execute)
    FORBIDDEN_PATTERNS = [
        r"rm\s+-rf\s+/\s*$",
        r"rm\s+-rf\s+/\*",
        r"rm\s+-rf\s+~",
        r">\s*/dev/sda",
        r"dd.*of=/dev/sd",
        r":(){.*};:",
    ]

    def __init__(
        self,
        log_file: str = "logs/actions.log",
        on_confirm_request: Optional[Callable[[str], bool]] = None
    ):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.on_confirm_request = on_confirm_request
        self.action_history: List[ActionLog] = []
        self._pending_confirmation: Optional[Dict] = None

        logger.info("System control initialized")

    def _log_action(
        self,
        action_type: str,
        command: str,
        success: bool,
        details: str,
        risk_level: ActionRisk
    ) -> None:
        """Log an action to file and memory."""
        entry = ActionLog(
            timestamp=datetime.now(),
            action_type=action_type,
            command=command,
            success=success,
            details=details,
            risk_level=risk_level
        )
        self.action_history.append(entry)

        # Keep only last 100 entries in memory
        if len(self.action_history) > 100:
            self.action_history = self.action_history[-100:]

        # Write to file
        with open(self.log_file, 'a') as f:
            f.write(
                f"{entry.timestamp.isoformat()} | "
                f"{entry.action_type} | "
                f"{entry.risk_level.value} | "
                f"{'OK' if entry.success else 'FAIL'} | "
                f"{entry.command} | "
                f"{entry.details}\n"
            )

    def _assess_risk(self, command: str) -> ActionRisk:
        """Assess the risk level of a command."""
        # Check forbidden patterns first
        for pattern in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return ActionRisk.FORBIDDEN

        # Check dangerous patterns
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                return ActionRisk.DANGEROUS

        return ActionRisk.SAFE

    def _find_application(self, app_name: str) -> Optional[str]:
        """Find the executable for an application."""
        app_lower = app_name.lower().strip()

        # Check aliases first
        if app_lower in self.APP_ALIASES:
            for cmd in self.APP_ALIASES[app_lower]:
                base_cmd = cmd.split()[0]
                if shutil.which(base_cmd):
                    return cmd

        # Try direct command
        if shutil.which(app_lower):
            return app_lower

        # Try with common suffixes
        for suffix in ['', '-bin', '.sh']:
            if shutil.which(app_lower + suffix):
                return app_lower + suffix

        return None

    # ==================== Application Control ====================

    def open_application(self, app_name: str) -> ActionResult:
        """Open an application by name."""
        cmd = self._find_application(app_name)

        if not cmd:
            self._log_action(
                "open_app", app_name, False,
                "Application not found", ActionRisk.SAFE
            )
            return ActionResult(
                success=False,
                message=f"No encontré la aplicación {app_name}.",
                action_type="open_app"
            )

        try:
            # Start application in background
            subprocess.Popen(
                cmd.split(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            self._log_action(
                "open_app", cmd, True,
                f"Opened {app_name}", ActionRisk.SAFE
            )

            return ActionResult(
                success=True,
                message=f"Abriendo {app_name}.",
                action_type="open_app"
            )

        except Exception as e:
            self._log_action(
                "open_app", cmd, False,
                str(e), ActionRisk.SAFE
            )
            return ActionResult(
                success=False,
                message=f"Error al abrir {app_name}: {e}",
                action_type="open_app"
            )

    def close_application(self, app_name: str) -> ActionResult:
        """Close an application by name."""
        app_lower = app_name.lower().strip()

        # Try to find the process
        try:
            # Use pkill for graceful termination
            result = subprocess.run(
                ["pkill", "-f", app_lower],
                capture_output=True,
                timeout=5
            )

            if result.returncode == 0:
                self._log_action(
                    "close_app", app_lower, True,
                    f"Closed {app_name}", ActionRisk.MODERATE
                )
                return ActionResult(
                    success=True,
                    message=f"Cerrando {app_name}.",
                    action_type="close_app"
                )
            else:
                # Try wmctrl if available
                if shutil.which("wmctrl"):
                    result = subprocess.run(
                        ["wmctrl", "-c", app_name],
                        capture_output=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        self._log_action(
                            "close_app", app_name, True,
                            "Closed via wmctrl", ActionRisk.MODERATE
                        )
                        return ActionResult(
                            success=True,
                            message=f"Cerrando {app_name}.",
                            action_type="close_app"
                        )

                self._log_action(
                    "close_app", app_lower, False,
                    "Application not running", ActionRisk.SAFE
                )
                return ActionResult(
                    success=False,
                    message=f"No encontré {app_name} ejecutándose.",
                    action_type="close_app"
                )

        except subprocess.TimeoutExpired:
            return ActionResult(
                success=False,
                message=f"Tiempo agotado al cerrar {app_name}.",
                action_type="close_app"
            )
        except Exception as e:
            self._log_action(
                "close_app", app_lower, False,
                str(e), ActionRisk.SAFE
            )
            return ActionResult(
                success=False,
                message=f"Error al cerrar {app_name}.",
                action_type="close_app"
            )

    # ==================== Volume Control ====================

    def set_volume(self, level: int) -> ActionResult:
        """Set volume to a specific level (0-100)."""
        level = max(0, min(100, level))

        # Try pactl first (PulseAudio)
        if shutil.which("pactl"):
            try:
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{level}%"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                self._log_action(
                    "volume", f"set {level}%", True,
                    f"Volume set to {level}%", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Volumen ajustado al {level}%.",
                    action_type="volume"
                )
            except Exception as e:
                logger.debug(f"pactl failed: {e}")

        # Try amixer (ALSA)
        if shutil.which("amixer"):
            try:
                subprocess.run(
                    ["amixer", "set", "Master", f"{level}%"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                self._log_action(
                    "volume", f"set {level}%", True,
                    f"Volume set to {level}%", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Volumen ajustado al {level}%.",
                    action_type="volume"
                )
            except Exception as e:
                logger.debug(f"amixer failed: {e}")

        self._log_action(
            "volume", f"set {level}%", False,
            "No audio control available", ActionRisk.SAFE
        )
        return ActionResult(
            success=False,
            message="No pude ajustar el volumen. No encontré control de audio.",
            action_type="volume"
        )

    def change_volume(self, delta: int) -> ActionResult:
        """Change volume by a relative amount."""
        sign = "+" if delta > 0 else "-"
        amount = abs(delta)

        if shutil.which("pactl"):
            try:
                subprocess.run(
                    ["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{sign}{amount}%"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                direction = "subido" if delta > 0 else "bajado"
                self._log_action(
                    "volume", f"change {sign}{amount}%", True,
                    f"Volume changed by {delta}%", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Volumen {direction}.",
                    action_type="volume"
                )
            except Exception as e:
                logger.debug(f"pactl failed: {e}")

        if shutil.which("amixer"):
            try:
                subprocess.run(
                    ["amixer", "set", "Master", f"{amount}%{sign}"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                direction = "subido" if delta > 0 else "bajado"
                self._log_action(
                    "volume", f"change {sign}{amount}%", True,
                    f"Volume changed by {delta}%", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Volumen {direction}.",
                    action_type="volume"
                )
            except Exception as e:
                logger.debug(f"amixer failed: {e}")

        return ActionResult(
            success=False,
            message="No pude ajustar el volumen.",
            action_type="volume"
        )

    def mute(self, mute: bool = True) -> ActionResult:
        """Mute or unmute audio."""
        state = "1" if mute else "0"
        action = "silenciado" if mute else "activado"

        if shutil.which("pactl"):
            try:
                subprocess.run(
                    ["pactl", "set-sink-mute", "@DEFAULT_SINK@", state],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                self._log_action(
                    "volume", f"mute={mute}", True,
                    f"Audio {'muted' if mute else 'unmuted'}", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Audio {action}.",
                    action_type="volume"
                )
            except Exception as e:
                logger.debug(f"pactl failed: {e}")

        if shutil.which("amixer"):
            try:
                toggle = "mute" if mute else "unmute"
                subprocess.run(
                    ["amixer", "set", "Master", toggle],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                self._log_action(
                    "volume", f"mute={mute}", True,
                    f"Audio {'muted' if mute else 'unmuted'}", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Audio {action}.",
                    action_type="volume"
                )
            except Exception as e:
                logger.debug(f"amixer failed: {e}")

        return ActionResult(
            success=False,
            message="No pude controlar el audio.",
            action_type="volume"
        )

    def get_volume(self) -> Optional[int]:
        """Get current volume level."""
        if shutil.which("pactl"):
            try:
                result = subprocess.run(
                    ["pactl", "get-sink-volume", "@DEFAULT_SINK@"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                match = re.search(r'(\d+)%', result.stdout)
                if match:
                    return int(match.group(1))
            except Exception:
                pass

        if shutil.which("amixer"):
            try:
                result = subprocess.run(
                    ["amixer", "get", "Master"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                match = re.search(r'\[(\d+)%\]', result.stdout)
                if match:
                    return int(match.group(1))
            except Exception:
                pass

        return None

    # ==================== Brightness Control ====================

    def _get_brightness_path(self) -> Optional[Path]:
        """Find the brightness control path."""
        backlight_path = Path("/sys/class/backlight")
        if backlight_path.exists():
            for device in backlight_path.iterdir():
                brightness_file = device / "brightness"
                if brightness_file.exists():
                    return device
        return None

    def set_brightness(self, level: int) -> ActionResult:
        """Set screen brightness (0-100)."""
        level = max(0, min(100, level))

        # Try brightnessctl first
        if shutil.which("brightnessctl"):
            try:
                subprocess.run(
                    ["brightnessctl", "set", f"{level}%"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                self._log_action(
                    "brightness", f"set {level}%", True,
                    f"Brightness set to {level}%", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Brillo ajustado al {level}%.",
                    action_type="brightness"
                )
            except Exception as e:
                logger.debug(f"brightnessctl failed: {e}")

        # Try xrandr
        if shutil.which("xrandr"):
            try:
                # Get primary display
                result = subprocess.run(
                    ["xrandr", "--query"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                match = re.search(r'^(\S+) connected primary', result.stdout, re.MULTILINE)
                if match:
                    display = match.group(1)
                    brightness = level / 100.0
                    subprocess.run(
                        ["xrandr", "--output", display, "--brightness", str(brightness)],
                        check=True,
                        capture_output=True,
                        timeout=5
                    )
                    self._log_action(
                        "brightness", f"set {level}%", True,
                        f"Brightness set to {level}%", ActionRisk.SAFE
                    )
                    return ActionResult(
                        success=True,
                        message=f"Brillo ajustado al {level}%.",
                        action_type="brightness"
                    )
            except Exception as e:
                logger.debug(f"xrandr failed: {e}")

        self._log_action(
            "brightness", f"set {level}%", False,
            "No brightness control available", ActionRisk.SAFE
        )
        return ActionResult(
            success=False,
            message="No pude ajustar el brillo. Control no disponible.",
            action_type="brightness"
        )

    def change_brightness(self, delta: int) -> ActionResult:
        """Change brightness by a relative amount."""
        if shutil.which("brightnessctl"):
            try:
                sign = "+" if delta > 0 else "-"
                amount = abs(delta)
                subprocess.run(
                    ["brightnessctl", "set", f"{amount}%{sign}"],
                    check=True,
                    capture_output=True,
                    timeout=5
                )
                direction = "aumentado" if delta > 0 else "reducido"
                self._log_action(
                    "brightness", f"change {delta}%", True,
                    f"Brightness changed by {delta}%", ActionRisk.SAFE
                )
                return ActionResult(
                    success=True,
                    message=f"Brillo {direction}.",
                    action_type="brightness"
                )
            except Exception as e:
                logger.debug(f"brightnessctl failed: {e}")

        return ActionResult(
            success=False,
            message="No pude ajustar el brillo.",
            action_type="brightness"
        )

    # ==================== Terminal Commands ====================

    def execute_command(
        self,
        command: str,
        force: bool = False
    ) -> ActionResult:
        """Execute a terminal command with safety checks."""
        risk = self._assess_risk(command)

        # Forbidden commands are never executed
        if risk == ActionRisk.FORBIDDEN:
            self._log_action(
                "command", command, False,
                "Forbidden command blocked", ActionRisk.FORBIDDEN
            )
            return ActionResult(
                success=False,
                message="Me temo que no puedo ejecutar ese comando, señor. Es demasiado peligroso.",
                action_type="command"
            )

        # Dangerous commands need confirmation
        if risk == ActionRisk.DANGEROUS and not force:
            self._pending_confirmation = {
                "command": command,
                "action": "execute_command"
            }
            return ActionResult(
                success=False,
                message=f"Este comando podría ser peligroso: {command}. ¿Está seguro, señor?",
                action_type="command",
                required_confirmation=True
            )

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            success = result.returncode == 0
            output = result.stdout[:200] if result.stdout else result.stderr[:200]

            self._log_action(
                "command", command, success,
                output or "Command executed", risk
            )

            if success:
                return ActionResult(
                    success=True,
                    message="Comando ejecutado.",
                    action_type="command",
                    details=output
                )
            else:
                return ActionResult(
                    success=False,
                    message=f"El comando falló: {result.stderr[:100]}",
                    action_type="command"
                )

        except subprocess.TimeoutExpired:
            self._log_action(
                "command", command, False,
                "Timeout", risk
            )
            return ActionResult(
                success=False,
                message="El comando tardó demasiado y fue cancelado.",
                action_type="command"
            )
        except Exception as e:
            self._log_action(
                "command", command, False,
                str(e), risk
            )
            return ActionResult(
                success=False,
                message=f"Error al ejecutar el comando: {e}",
                action_type="command"
            )

    def confirm_pending_action(self, confirmed: bool) -> ActionResult:
        """Confirm or cancel a pending dangerous action."""
        if not self._pending_confirmation:
            return ActionResult(
                success=False,
                message="No hay ninguna acción pendiente de confirmación.",
                action_type="confirm"
            )

        pending = self._pending_confirmation
        self._pending_confirmation = None

        if not confirmed:
            self._log_action(
                pending["action"], pending.get("command", ""),
                False, "Cancelled by user", ActionRisk.DANGEROUS
            )
            return ActionResult(
                success=True,
                message="Entendido. Acción cancelada.",
                action_type="confirm"
            )

        # Execute the pending action
        if pending["action"] == "execute_command":
            return self.execute_command(pending["command"], force=True)

        return ActionResult(
            success=False,
            message="Acción desconocida.",
            action_type="confirm"
        )

    def has_pending_confirmation(self) -> bool:
        """Check if there's a pending confirmation."""
        return self._pending_confirmation is not None

    # ==================== Action History ====================

    def get_recent_actions(self, limit: int = 10) -> List[ActionLog]:
        """Get recent action history."""
        return self.action_history[-limit:]

    def get_action_summary(self) -> str:
        """Get a summary of recent actions."""
        recent = self.get_recent_actions(5)
        if not recent:
            return "No hay acciones recientes registradas."

        lines = ["Acciones recientes:"]
        for action in recent:
            status = "OK" if action.success else "FAIL"
            lines.append(
                f"- {action.action_type}: {action.command} [{status}]"
            )
        return "\n".join(lines)


class ControlQueryHandler:
    """Handles control-related queries from user input."""

    # Patterns for control commands
    OPEN_PATTERNS = [
        r"abre\s+(?:el\s+|la\s+)?(.+)",
        r"abrir\s+(.+)",
        r"ejecuta\s+(.+)",
        r"lanza\s+(.+)",
        r"inicia\s+(.+)",
    ]

    CLOSE_PATTERNS = [
        r"cierra\s+(?:el\s+|la\s+)?(.+)",
        r"cerrar\s+(.+)",
        r"termina\s+(.+)",
        r"mata\s+(.+)",
    ]

    VOLUME_PATTERNS = [
        (r"sube\s+(?:el\s+)?volumen", "up", 10),
        (r"baja\s+(?:el\s+)?volumen", "down", -10),
        (r"m[aá]s\s+volumen", "up", 10),
        (r"menos\s+volumen", "down", -10),
        (r"silencia", "mute", None),
        (r"quita\s+(?:el\s+)?silencio", "unmute", None),
        (r"volumen\s+(?:al\s+)?(\d+)", "set", None),
        (r"pon\s+(?:el\s+)?volumen\s+(?:al\s+|a\s+)?(\d+)", "set", None),
    ]

    BRIGHTNESS_PATTERNS = [
        (r"sube\s+(?:el\s+)?brillo", "up", 10),
        (r"baja\s+(?:el\s+)?brillo", "down", -10),
        (r"m[aá]s\s+brillo", "up", 10),
        (r"menos\s+brillo", "down", -10),
        (r"brillo\s+(?:al\s+)?(\d+)", "set", None),
        (r"pon\s+(?:el\s+)?brillo\s+(?:al\s+|a\s+)?(\d+)", "set", None),
    ]

    CONFIRM_PATTERNS = [
        (r"^s[ií]$", True),
        (r"^confirmo$", True),
        (r"^adelante$", True),
        (r"^procede$", True),
        (r"^no$", False),
        (r"^cancela$", False),
        (r"^olvídalo$", False),
    ]

    def __init__(self, control: Optional[SystemControl] = None):
        self.control = control or SystemControl()

    def process_command(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Process a control command.

        Returns:
            Tuple of (was_control_command, response)
        """
        input_lower = user_input.lower().strip()

        # Check for pending confirmation first
        if self.control.has_pending_confirmation():
            for pattern, confirmed in self.CONFIRM_PATTERNS:
                if re.match(pattern, input_lower):
                    result = self.control.confirm_pending_action(confirmed)
                    return (True, result.message)

        # Check open commands
        for pattern in self.OPEN_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                app_name = match.group(1).strip()
                result = self.control.open_application(app_name)
                return (True, result.message)

        # Check close commands
        for pattern in self.CLOSE_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                app_name = match.group(1).strip()
                result = self.control.close_application(app_name)
                return (True, result.message)

        # Check volume commands
        for pattern, action, default_value in self.VOLUME_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                if action == "mute":
                    result = self.control.mute(True)
                elif action == "unmute":
                    result = self.control.mute(False)
                elif action == "set":
                    level = int(match.group(1)) if match.lastindex else 50
                    result = self.control.set_volume(level)
                elif action == "up":
                    result = self.control.change_volume(default_value)
                elif action == "down":
                    result = self.control.change_volume(default_value)
                else:
                    continue
                return (True, result.message)

        # Check brightness commands
        for pattern, action, default_value in self.BRIGHTNESS_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                if action == "set":
                    level = int(match.group(1)) if match.lastindex else 50
                    result = self.control.set_brightness(level)
                elif action == "up":
                    result = self.control.change_brightness(default_value)
                elif action == "down":
                    result = self.control.change_brightness(default_value)
                else:
                    continue
                return (True, result.message)

        return (False, None)


# Singleton instances
_control_instance: Optional[SystemControl] = None
_handler_instance: Optional[ControlQueryHandler] = None


def get_system_control(
    log_file: str = "logs/actions.log"
) -> SystemControl:
    """Get or create the system control instance."""
    global _control_instance

    if _control_instance is None:
        _control_instance = SystemControl(log_file=log_file)

    return _control_instance


def get_control_handler() -> ControlQueryHandler:
    """Get or create the control handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = ControlQueryHandler(get_system_control())

    return _handler_instance
