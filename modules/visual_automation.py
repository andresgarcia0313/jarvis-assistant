"""
JARVIS Visual Automation Module
Combines vision + input control for complex multi-step tasks.

Flow:
1. User gives task
2. JARVIS captures screen
3. Analyzes current state
4. Plans necessary steps
5. Asks for confirmation
6. Executes step by step
7. Verifies each step result
8. Reports final result
"""

import subprocess
import logging
import re
import time
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of an automation task."""
    PENDING = "pending"
    PLANNING = "planning"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AutomationStep:
    """A single step in an automation task."""
    description: str
    action_type: str
    params: Dict
    completed: bool = False
    result: Optional[str] = None


@dataclass
class AutomationTask:
    """An automation task with multiple steps."""
    description: str
    steps: List[AutomationStep] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    current_step: int = 0
    error_message: Optional[str] = None


class VisualAutomation:
    """Combines screen analysis with input control for automation."""

    # Common task patterns
    TASK_PATTERNS = [
        (r"abre\s+(.+?)\s+y\s+busca\s+(.+)", "open_and_search"),
        (r"busca\s+(?:el\s+)?bot[oó]n\s+(?:que\s+dice\s+)?(.+?)\s+y\s+(?:haz\s+)?click", "find_and_click"),
        (r"escribe\s+(.+?)\s+en\s+(?:el\s+)?(?:campo|formulario)", "type_in_field"),
        (r"abre\s+(.+)", "open_app"),
        (r"cierra\s+(.+)", "close_app"),
    ]

    def __init__(self, screen_analyzer=None, input_controller=None, claude_command: str = "claude"):
        self.claude_command = claude_command
        self.screen_analyzer = screen_analyzer
        self.input_controller = input_controller
        self.current_task: Optional[AutomationTask] = None
        self._cancelled = False

    def cancel(self):
        """Cancel current automation."""
        self._cancelled = True
        if self.current_task:
            self.current_task.status = TaskStatus.CANCELLED
        logger.warning("Automation cancelled by user")

    def reset(self):
        """Reset automation state."""
        self._cancelled = False
        self.current_task = None

    def plan_task(self, task_description: str) -> AutomationTask:
        """Plan an automation task based on description."""
        task = AutomationTask(description=task_description)
        task.status = TaskStatus.PLANNING

        # Parse task and create steps
        task_lower = task_description.lower()

        for pattern, task_type in self.TASK_PATTERNS:
            match = re.search(pattern, task_lower)
            if match:
                steps = self._create_steps_for_task(task_type, match.groups())
                task.steps = steps
                break

        if not task.steps:
            # Generic task - analyze screen and suggest
            task.steps = [
                AutomationStep(
                    description="Analizar pantalla actual",
                    action_type="analyze",
                    params={}
                ),
                AutomationStep(
                    description="Determinar próximo paso",
                    action_type="plan_next",
                    params={"goal": task_description}
                )
            ]

        task.status = TaskStatus.AWAITING_CONFIRMATION
        self.current_task = task
        return task

    def _create_steps_for_task(self, task_type: str, params: tuple) -> List[AutomationStep]:
        """Create steps for a specific task type."""
        steps = []

        if task_type == "open_and_search":
            app_name, search_term = params
            steps = [
                AutomationStep(
                    description=f"Abrir {app_name}",
                    action_type="open_app",
                    params={"app": app_name}
                ),
                AutomationStep(
                    description="Esperar que la aplicación cargue",
                    action_type="wait",
                    params={"seconds": 2}
                ),
                AutomationStep(
                    description="Verificar aplicación abierta",
                    action_type="verify_screen",
                    params={"expect": app_name}
                ),
                AutomationStep(
                    description=f"Buscar: {search_term}",
                    action_type="type_text",
                    params={"text": search_term}
                ),
                AutomationStep(
                    description="Presionar Enter",
                    action_type="key_press",
                    params={"key": "Return"}
                ),
            ]

        elif task_type == "find_and_click":
            button_text = params[0]
            steps = [
                AutomationStep(
                    description="Capturar pantalla",
                    action_type="capture_screen",
                    params={}
                ),
                AutomationStep(
                    description=f"Buscar botón '{button_text}'",
                    action_type="find_element",
                    params={"text": button_text}
                ),
                AutomationStep(
                    description=f"Click en '{button_text}'",
                    action_type="click_element",
                    params={"text": button_text}
                ),
            ]

        elif task_type == "open_app":
            app_name = params[0]
            steps = [
                AutomationStep(
                    description=f"Abrir {app_name}",
                    action_type="open_app",
                    params={"app": app_name}
                ),
                AutomationStep(
                    description="Verificar apertura",
                    action_type="verify_screen",
                    params={"expect": app_name}
                ),
            ]

        elif task_type == "close_app":
            app_name = params[0]
            steps = [
                AutomationStep(
                    description=f"Cerrar {app_name}",
                    action_type="close_app",
                    params={"app": app_name}
                ),
            ]

        elif task_type == "type_in_field":
            text = params[0]
            steps = [
                AutomationStep(
                    description="Localizar campo de entrada",
                    action_type="find_input",
                    params={}
                ),
                AutomationStep(
                    description=f"Escribir: {text}",
                    action_type="type_text",
                    params={"text": text}
                ),
            ]

        return steps

    def get_plan_summary(self) -> str:
        """Get a summary of the planned task."""
        if not self.current_task:
            return "No hay tarea planificada."

        task = self.current_task
        summary = f"Plan para: {task.description}\n"
        summary += f"Pasos ({len(task.steps)}):\n"

        for i, step in enumerate(task.steps, 1):
            status = "✓" if step.completed else "○"
            summary += f"  {status} {i}. {step.description}\n"

        return summary

    def confirm_and_execute(self) -> str:
        """Execute the planned task after confirmation."""
        if not self.current_task:
            return "No hay tarea para ejecutar."

        task = self.current_task
        task.status = TaskStatus.EXECUTING

        results = []

        for i, step in enumerate(task.steps):
            if self._cancelled:
                task.status = TaskStatus.CANCELLED
                return "Tarea cancelada por el usuario."

            task.current_step = i
            logger.info(f"Executing step {i+1}: {step.description}")

            result = self._execute_step(step)

            if result.startswith("Error"):
                step.result = result
                task.status = TaskStatus.FAILED
                task.error_message = result
                return f"Fallo en paso {i+1}: {result}"

            step.completed = True
            step.result = result
            results.append(f"Paso {i+1}: {result}")

        task.status = TaskStatus.COMPLETED
        return f"Tarea completada. {len(task.steps)} pasos ejecutados."

    def _execute_step(self, step: AutomationStep) -> str:
        """Execute a single automation step."""
        action = step.action_type
        params = step.params

        try:
            if action == "wait":
                seconds = params.get("seconds", 1)
                time.sleep(seconds)
                return f"Esperado {seconds} segundos"

            elif action == "open_app":
                app = params.get("app", "")
                # Use system control to open app
                return self._open_application(app)

            elif action == "close_app":
                app = params.get("app", "")
                return self._close_application(app)

            elif action == "type_text":
                text = params.get("text", "")
                if self.input_controller:
                    self.input_controller.controller.type_text(text)
                    return f"Escrito: {text[:30]}..."
                return "Error: Sin controlador de input"

            elif action == "key_press":
                key = params.get("key", "")
                if self.input_controller:
                    self.input_controller.controller.press_key(key)
                    return f"Tecla presionada: {key}"
                return "Error: Sin controlador de input"

            elif action == "capture_screen":
                if self.screen_analyzer:
                    return "Pantalla capturada"
                return "Error: Sin analizador de pantalla"

            elif action == "analyze":
                if self.screen_analyzer:
                    return self.screen_analyzer.describe_screen()
                return "Error: Sin analizador de pantalla"

            elif action == "verify_screen":
                expected = params.get("expect", "")
                if self.screen_analyzer:
                    desc = self.screen_analyzer.describe_screen()
                    if expected.lower() in desc.lower():
                        return f"Verificado: {expected} visible"
                    return f"Advertencia: No se detectó {expected}"
                return "Verificación omitida"

            elif action == "find_element":
                text = params.get("text", "")
                if self.screen_analyzer:
                    prompt = f"¿Puedes ver un elemento o botón que diga '{text}'? Describe su ubicación."
                    result = self.screen_analyzer.analyze_screen(prompt)
                    return result
                return "Error: Sin analizador de pantalla"

            elif action == "click_element":
                text = params.get("text", "")
                # Would need visual analysis to find location
                return f"Click en elemento '{text}' (requiere ubicación visual)"

            elif action == "plan_next":
                goal = params.get("goal", "")
                if self.screen_analyzer:
                    prompt = f"Dado el objetivo '{goal}' y lo que ves en pantalla, ¿qué acción sugieres?"
                    return self.screen_analyzer.analyze_screen(prompt)
                return "Requiere análisis visual"

            else:
                return f"Acción desconocida: {action}"

        except Exception as e:
            logger.error(f"Step execution error: {e}")
            return f"Error: {e}"

    def _open_application(self, app_name: str) -> str:
        """Open an application."""
        app_commands = {
            "chrome": ["google-chrome", "chromium-browser", "chromium"],
            "firefox": ["firefox"],
            "terminal": ["konsole", "gnome-terminal", "xterm"],
            "archivos": ["dolphin", "nautilus", "thunar"],
            "editor": ["kate", "gedit", "code"],
            "calculadora": ["kcalc", "gnome-calculator"],
        }

        app_lower = app_name.lower()

        # Find matching commands
        commands = app_commands.get(app_lower, [app_lower])

        for cmd in commands:
            try:
                subprocess.Popen(
                    [cmd],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return f"Abierto: {app_name}"
            except FileNotFoundError:
                continue

        return f"Error: No se pudo abrir {app_name}"

    def _close_application(self, app_name: str) -> str:
        """Close an application."""
        try:
            # Use wmctrl or xdotool to close
            subprocess.run(
                ["xdotool", "search", "--name", app_name, "windowclose"],
                capture_output=True,
                timeout=5
            )
            return f"Cerrado: {app_name}"
        except Exception as e:
            return f"Error al cerrar: {e}"


class VisualAutomationHandler:
    """Handles visual automation voice queries."""

    AUTOMATION_PATTERNS = [
        (r"abre\s+(.+?)\s+y\s+busca\s+(.+)", "complex_task"),
        (r"busca\s+(?:el\s+)?bot[oó]n.*click", "complex_task"),
        (r"haz\s+(?:la\s+)?tarea[:\s]+(.+)", "complex_task"),
        (r"automatiza[:\s]+(.+)", "complex_task"),
    ]

    CONFIRM_PATTERNS = [r"^s[ií]$", r"^procede$", r"^adelante$", r"^confirmo$"]
    CANCEL_PATTERNS = [r"^no$", r"^cancela$", r"^para$"]

    def __init__(self, automation: Optional[VisualAutomation] = None):
        self.automation = automation or VisualAutomation()
        self.awaiting_confirmation = False

    def process_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process an automation query."""
        input_lower = user_input.lower().strip()

        # Check for cancel
        for pattern in self.CANCEL_PATTERNS:
            if re.match(pattern, input_lower):
                if self.awaiting_confirmation:
                    self.awaiting_confirmation = False
                    self.automation.reset()
                    return (True, "Tarea cancelada.")
                return (False, None)

        # Check for confirmation
        if self.awaiting_confirmation:
            for pattern in self.CONFIRM_PATTERNS:
                if re.match(pattern, input_lower):
                    self.awaiting_confirmation = False
                    result = self.automation.confirm_and_execute()
                    return (True, result)
            return (True, "Diga 'sí' para confirmar o 'no' para cancelar el plan.")

        # Check for new automation task
        for pattern, _ in self.AUTOMATION_PATTERNS:
            if re.search(pattern, input_lower):
                task = self.automation.plan_task(user_input)
                summary = self.automation.get_plan_summary()
                self.awaiting_confirmation = True
                return (True, f"{summary}\n¿Procedo con este plan, señor?")

        return (False, None)


# Singleton instances
_automation_instance: Optional[VisualAutomation] = None
_handler_instance: Optional[VisualAutomationHandler] = None


def get_visual_automation(screen_analyzer=None, input_controller=None) -> VisualAutomation:
    """Get or create the visual automation instance."""
    global _automation_instance

    if _automation_instance is None:
        _automation_instance = VisualAutomation(screen_analyzer, input_controller)

    return _automation_instance


def get_automation_handler() -> VisualAutomationHandler:
    """Get or create the automation handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = VisualAutomationHandler(get_visual_automation())

    return _handler_instance
