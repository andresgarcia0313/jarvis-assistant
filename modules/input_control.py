"""
JARVIS Input Control Module
Controls mouse and keyboard using xdotool or similar tools.

SECURITY CRITICAL:
- All actions require explicit user confirmation
- Safety word "alto" or "para" stops all actions immediately
- Detailed logging of all input actions
- Demo mode available (shows what would happen without doing it)
- Action limits per sequence
"""

import subprocess
import shutil
import logging
import re
import time
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of input actions."""
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    KEY_TYPE = "key_type"
    KEY_PRESS = "key_press"
    KEY_COMBO = "key_combo"


@dataclass
class InputAction:
    """Represents a pending input action."""
    action_type: ActionType
    description: str
    params: Dict
    confirmed: bool = False


@dataclass
class ActionResult:
    """Result of an input action."""
    success: bool
    message: str
    action_type: Optional[ActionType] = None


class InputController:
    """Low-level input control using xdotool."""

    # Key name mappings (Spanish to xdotool)
    KEY_MAPPINGS = {
        "control": "ctrl",
        "alt": "alt",
        "shift": "shift",
        "super": "super",
        "windows": "super",
        "enter": "Return",
        "intro": "Return",
        "escape": "Escape",
        "escapar": "Escape",
        "espacio": "space",
        "tab": "Tab",
        "tabulador": "Tab",
        "borrar": "BackSpace",
        "suprimir": "Delete",
        "inicio": "Home",
        "fin": "End",
        "arriba": "Up",
        "abajo": "Down",
        "izquierda": "Left",
        "derecha": "Right",
        "página arriba": "Page_Up",
        "página abajo": "Page_Down",
    }

    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        self.tool = self._detect_tool()
        self.action_log: List[str] = []
        self._stopped = False

        if not self.tool:
            logger.warning("No input control tool available")

    def _detect_tool(self) -> Optional[str]:
        """Detect available input control tool."""
        tools = ["xdotool", "xte"]
        for tool in tools:
            if shutil.which(tool):
                logger.info(f"Using input tool: {tool}")
                return tool
        return None

    def is_available(self) -> bool:
        """Check if input control is available."""
        return self.tool is not None

    def stop(self):
        """Emergency stop all actions."""
        self._stopped = True
        logger.warning("INPUT CONTROL STOPPED BY SAFETY COMMAND")

    def reset(self):
        """Reset stopped state."""
        self._stopped = False

    def _log_action(self, action: str):
        """Log an action."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] {action}"
        self.action_log.append(entry)
        logger.info(f"INPUT ACTION: {action}")

    def _run_xdotool(self, *args) -> ActionResult:
        """Run xdotool command."""
        if self._stopped:
            return ActionResult(False, "Acciones detenidas por comando de seguridad")

        if self.demo_mode:
            cmd = f"xdotool {' '.join(args)}"
            self._log_action(f"[DEMO] {cmd}")
            return ActionResult(True, f"Demo: ejecutaría '{cmd}'")

        try:
            result = subprocess.run(
                ["xdotool"] + list(args),
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                self._log_action(f"xdotool {' '.join(args)}")
                return ActionResult(True, "Acción completada")
            else:
                return ActionResult(False, f"Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            return ActionResult(False, "La acción tardó demasiado")
        except Exception as e:
            return ActionResult(False, f"Error: {e}")

    def get_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        try:
            result = subprocess.run(
                ["xdotool", "getmouselocation"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                # Parse "x:123 y:456 screen:0 window:12345"
                match = re.search(r'x:(\d+)\s+y:(\d+)', result.stdout)
                if match:
                    return int(match.group(1)), int(match.group(2))
        except Exception:
            pass
        return 0, 0

    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen dimensions."""
        try:
            result = subprocess.run(
                ["xdotool", "getdisplaygeometry"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                parts = result.stdout.strip().split()
                if len(parts) >= 2:
                    return int(parts[0]), int(parts[1])
        except Exception:
            pass
        return 1920, 1080  # Default fallback

    def move_mouse(self, x: int, y: int, relative: bool = False) -> ActionResult:
        """Move mouse to position."""
        if relative:
            return self._run_xdotool("mousemove_relative", str(x), str(y))
        else:
            return self._run_xdotool("mousemove", str(x), str(y))

    def move_mouse_to_region(self, region: str) -> ActionResult:
        """Move mouse to named region (arriba, abajo, izquierda, derecha, centro)."""
        width, height = self.get_screen_size()

        regions = {
            "centro": (width // 2, height // 2),
            "arriba": (width // 2, height // 4),
            "abajo": (width // 2, 3 * height // 4),
            "izquierda": (width // 4, height // 2),
            "derecha": (3 * width // 4, height // 2),
            "arriba izquierda": (width // 4, height // 4),
            "arriba derecha": (3 * width // 4, height // 4),
            "abajo izquierda": (width // 4, 3 * height // 4),
            "abajo derecha": (3 * width // 4, 3 * height // 4),
        }

        region_lower = region.lower().strip()
        if region_lower in regions:
            x, y = regions[region_lower]
            return self.move_mouse(x, y)

        return ActionResult(False, f"Región no reconocida: {region}")

    def click(self, button: str = "left", count: int = 1) -> ActionResult:
        """Perform mouse click."""
        button_map = {
            "left": "1", "izquierdo": "1", "izquierda": "1",
            "right": "3", "derecho": "3", "derecha": "3",
            "middle": "2", "medio": "2", "central": "2",
        }

        btn = button_map.get(button.lower(), "1")

        if count == 2:
            return self._run_xdotool("click", "--repeat", "2", "--delay", "100", btn)
        else:
            return self._run_xdotool("click", btn)

    def scroll(self, direction: str, amount: int = 3) -> ActionResult:
        """Scroll mouse wheel."""
        if direction.lower() in ["arriba", "up", "subir"]:
            return self._run_xdotool("click", "--repeat", str(amount), "4")
        elif direction.lower() in ["abajo", "down", "bajar"]:
            return self._run_xdotool("click", "--repeat", str(amount), "5")
        else:
            return ActionResult(False, f"Dirección de scroll no reconocida: {direction}")

    def type_text(self, text: str, delay: int = 50) -> ActionResult:
        """Type text using keyboard."""
        return self._run_xdotool("type", "--delay", str(delay), text)

    def press_key(self, key: str) -> ActionResult:
        """Press a single key."""
        mapped_key = self.KEY_MAPPINGS.get(key.lower(), key)
        return self._run_xdotool("key", mapped_key)

    def press_combo(self, *keys) -> ActionResult:
        """Press key combination."""
        mapped_keys = [self.KEY_MAPPINGS.get(k.lower(), k) for k in keys]
        combo = "+".join(mapped_keys)
        return self._run_xdotool("key", combo)


class SafeInputController:
    """Safe wrapper that requires confirmation for actions."""

    SAFETY_WORDS = ["alto", "para", "stop", "detente", "cancelar"]
    MAX_ACTIONS_PER_SEQUENCE = 10

    def __init__(self, demo_mode: bool = False):
        self.controller = InputController(demo_mode)
        self.pending_action: Optional[InputAction] = None
        self.actions_in_sequence = 0

    def is_available(self) -> bool:
        return self.controller.is_available()

    def is_safety_word(self, text: str) -> bool:
        """Check if text contains safety word."""
        text_lower = text.lower().strip()
        return any(word in text_lower for word in self.SAFETY_WORDS)

    def emergency_stop(self):
        """Emergency stop all actions."""
        self.controller.stop()
        self.pending_action = None
        self.actions_in_sequence = 0

    def reset(self):
        """Reset controller state."""
        self.controller.reset()
        self.actions_in_sequence = 0

    def prepare_action(self, action: InputAction) -> str:
        """Prepare an action and return confirmation message."""
        if self.actions_in_sequence >= self.MAX_ACTIONS_PER_SEQUENCE:
            return "He alcanzado el límite de acciones por secuencia. Diga 'reset' para continuar."

        self.pending_action = action
        return f"Voy a {action.description}. ¿Procedo, señor?"

    def confirm_and_execute(self) -> ActionResult:
        """Execute pending action after confirmation."""
        if not self.pending_action:
            return ActionResult(False, "No hay acción pendiente")

        action = self.pending_action
        self.pending_action = None
        self.actions_in_sequence += 1

        result = self._execute_action(action)
        return result

    def cancel_pending(self) -> str:
        """Cancel pending action."""
        if self.pending_action:
            desc = self.pending_action.description
            self.pending_action = None
            return f"Cancelado: {desc}"
        return "No hay acción pendiente para cancelar"

    def _execute_action(self, action: InputAction) -> ActionResult:
        """Execute an input action."""
        params = action.params

        if action.action_type == ActionType.MOUSE_MOVE:
            if "region" in params:
                return self.controller.move_mouse_to_region(params["region"])
            else:
                return self.controller.move_mouse(
                    params.get("x", 0),
                    params.get("y", 0),
                    params.get("relative", False)
                )

        elif action.action_type == ActionType.MOUSE_CLICK:
            return self.controller.click(
                params.get("button", "left"),
                params.get("count", 1)
            )

        elif action.action_type == ActionType.MOUSE_SCROLL:
            return self.controller.scroll(
                params.get("direction", "abajo"),
                params.get("amount", 3)
            )

        elif action.action_type == ActionType.KEY_TYPE:
            return self.controller.type_text(params.get("text", ""))

        elif action.action_type == ActionType.KEY_PRESS:
            return self.controller.press_key(params.get("key", ""))

        elif action.action_type == ActionType.KEY_COMBO:
            keys = params.get("keys", [])
            return self.controller.press_combo(*keys)

        return ActionResult(False, "Tipo de acción no reconocido")


class InputQueryHandler:
    """Handles input control voice queries."""

    # Mouse movement patterns
    MOUSE_MOVE_PATTERNS = [
        (r"mueve(?:\s+el)?\s+mouse\s+(?:a\s+)?(?:la\s+)?(.+)", "move_region"),
        (r"pon(?:\s+el)?\s+mouse\s+(?:en\s+)?(?:la\s+)?(.+)", "move_region"),
        (r"mouse\s+(?:a\s+)?(?:la\s+)?(.+)", "move_region"),
    ]

    # Click patterns
    CLICK_PATTERNS = [
        (r"(?:haz\s+)?click\s+derecho", "right_click"),
        (r"(?:haz\s+)?doble\s+click", "double_click"),
        (r"(?:haz\s+)?click(?:\s+izquierdo)?", "left_click"),
        (r"(?:haz\s+)?clic(?:\s+izquierdo)?", "left_click"),
    ]

    # Scroll patterns
    SCROLL_PATTERNS = [
        (r"(?:baja|scroll\s+(?:hacia\s+)?abajo|desplaza\s+abajo)", "scroll_down"),
        (r"(?:sube|scroll\s+(?:hacia\s+)?arriba|desplaza\s+arriba)", "scroll_up"),
        (r"baja\s+(?:la\s+)?p[aá]gina", "page_down"),
        (r"sube\s+(?:la\s+)?p[aá]gina", "page_up"),
    ]

    # Typing patterns
    TYPE_PATTERNS = [
        (r"escribe[:\s]+(.+)", "type"),
        (r"teclea[:\s]+(.+)", "type"),
        (r"escribe\s+comillas?\s+(.+)\s+comillas?", "type"),
    ]

    # Key combo patterns
    KEY_PATTERNS = [
        (r"presiona\s+(.+)", "key_combo"),
        (r"pulsa\s+(.+)", "key_combo"),
        (r"tecla\s+(.+)", "key_combo"),
    ]

    # Confirmation patterns
    CONFIRM_PATTERNS = [
        r"^s[ií]$",
        r"^procede$",
        r"^adelante$",
        r"^hazlo$",
        r"^ok$",
        r"^confirmo$",
        r"^afirmativo$",
    ]

    CANCEL_PATTERNS = [
        r"^no$",
        r"^cancela(?:r)?$",
        r"^olvida(?:lo)?$",
        r"^d[ée]jalo$",
    ]

    def __init__(self, controller: Optional[SafeInputController] = None):
        self.controller = controller or SafeInputController()
        self.awaiting_confirmation = False

    def process_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process an input control query."""
        input_lower = user_input.lower().strip()

        # Check for safety words first
        if self.controller.is_safety_word(input_lower):
            self.controller.emergency_stop()
            self.awaiting_confirmation = False
            return (True, "Entendido. Todas las acciones detenidas.")

        # Check for confirmation/cancellation if awaiting
        if self.awaiting_confirmation:
            return self._handle_confirmation(input_lower)

        # Check for reset
        if input_lower in ["reset", "reinicia", "reiniciar"]:
            self.controller.reset()
            return (True, "Control de input reiniciado.")

        # Parse input commands
        action = self._parse_input_command(input_lower, user_input)
        if action:
            confirmation_msg = self.controller.prepare_action(action)
            self.awaiting_confirmation = True
            return (True, confirmation_msg)

        return (False, None)

    def _handle_confirmation(self, input_lower: str) -> Tuple[bool, str]:
        """Handle confirmation or cancellation."""
        # Check for confirmation
        for pattern in self.CONFIRM_PATTERNS:
            if re.match(pattern, input_lower):
                self.awaiting_confirmation = False
                result = self.controller.confirm_and_execute()
                return (True, result.message)

        # Check for cancellation
        for pattern in self.CANCEL_PATTERNS:
            if re.match(pattern, input_lower):
                self.awaiting_confirmation = False
                msg = self.controller.cancel_pending()
                return (True, msg)

        # Still awaiting confirmation
        return (True, "No entendí. Diga 'sí' para confirmar o 'no' para cancelar.")

    def _parse_input_command(self, input_lower: str, original: str) -> Optional[InputAction]:
        """Parse input command and return action."""
        # Mouse move
        for pattern, cmd_type in self.MOUSE_MOVE_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                region = match.group(1).strip()
                return InputAction(
                    action_type=ActionType.MOUSE_MOVE,
                    description=f"mover el mouse a {region}",
                    params={"region": region}
                )

        # Clicks
        for pattern, cmd_type in self.CLICK_PATTERNS:
            if re.search(pattern, input_lower):
                if cmd_type == "right_click":
                    return InputAction(
                        action_type=ActionType.MOUSE_CLICK,
                        description="hacer click derecho",
                        params={"button": "right", "count": 1}
                    )
                elif cmd_type == "double_click":
                    return InputAction(
                        action_type=ActionType.MOUSE_CLICK,
                        description="hacer doble click",
                        params={"button": "left", "count": 2}
                    )
                else:
                    return InputAction(
                        action_type=ActionType.MOUSE_CLICK,
                        description="hacer click",
                        params={"button": "left", "count": 1}
                    )

        # Scroll
        for pattern, cmd_type in self.SCROLL_PATTERNS:
            if re.search(pattern, input_lower):
                direction = "arriba" if "up" in cmd_type or "arriba" in cmd_type else "abajo"
                amount = 5 if "page" in cmd_type else 3
                return InputAction(
                    action_type=ActionType.MOUSE_SCROLL,
                    description=f"hacer scroll hacia {direction}",
                    params={"direction": direction, "amount": amount}
                )

        # Typing
        for pattern, cmd_type in self.TYPE_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                # Use original to preserve case
                text_match = re.search(pattern.replace("(.+)", "(.+)"), original, re.IGNORECASE)
                text = text_match.group(1).strip() if text_match else match.group(1).strip()
                return InputAction(
                    action_type=ActionType.KEY_TYPE,
                    description=f"escribir '{text[:30]}{'...' if len(text) > 30 else ''}'",
                    params={"text": text}
                )

        # Key combos
        for pattern, cmd_type in self.KEY_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                keys_str = match.group(1).strip()
                # Parse keys (e.g., "control alt t" -> ["control", "alt", "t"])
                keys = re.split(r'\s+', keys_str)
                desc = " + ".join(keys)
                return InputAction(
                    action_type=ActionType.KEY_COMBO,
                    description=f"presionar {desc}",
                    params={"keys": keys}
                )

        return None


# Singleton instances
_controller_instance: Optional[SafeInputController] = None
_handler_instance: Optional[InputQueryHandler] = None


def get_input_controller(demo_mode: bool = False) -> SafeInputController:
    """Get or create the input controller instance."""
    global _controller_instance

    if _controller_instance is None:
        _controller_instance = SafeInputController(demo_mode)

    return _controller_instance


def get_input_handler() -> InputQueryHandler:
    """Get or create the input query handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = InputQueryHandler(get_input_controller())

    return _handler_instance
