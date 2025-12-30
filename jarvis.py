#!/usr/bin/env python3
"""
JARVIS - Voice Assistant for Kubuntu
Phase 2: Personality Integration

Main orchestrator that coordinates:
- Wake word detection
- Speech-to-Text
- Claude CLI integration with JARVIS personality
- Text-to-Speech
- Barge-in (interruption) support
"""

import sys
import signal
import logging
import threading
from pathlib import Path
from typing import Optional

import yaml

from modules.stt import SpeechToText
from modules.tts import TextToSpeech
from modules.wake_word import WakeWordDetector
from modules.cli_bridge import ClaudeBridge, ConversationManager
from modules.personality import JarvisPersonality
from modules.system_monitor import (
    SystemMonitor, SystemQueryHandler, AlertThresholds
)
from modules.system_control import SystemControl, ControlQueryHandler
from modules.reminders import ReminderManager, ReminderQueryHandler
from modules.calendar_integration import CalendarManager, CalendarQueryHandler
from modules.dev_tools import DevToolsManager, DevQueryHandler
from modules.screen_vision import ScreenAnalyzer, ScreenQueryHandler
from modules.camera_vision import CameraAnalyzer, CameraQueryHandler
from modules.input_control import SafeInputController, InputQueryHandler
from modules.visual_automation import VisualAutomation, VisualAutomationHandler
from memory import MemoryHandler, get_memory

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("JARVIS")


class Jarvis:
    """Main JARVIS orchestrator."""

    def __init__(self, config_path: str = "config.yaml"):
        self.running = False
        self.config = self._load_config(config_path)
        self.conversation = ConversationManager()

        # State flags
        self._interrupt_requested = False
        self._shutdown_requested = False
        self._pending_alerts: list = []

        # Initialize system monitor
        monitor_config = self.config.get("monitor", {})
        thresholds = AlertThresholds(
            cpu_percent=monitor_config.get("cpu_threshold", 90.0),
            cpu_sustained_minutes=monitor_config.get("cpu_sustained_minutes", 5),
            ram_percent=monitor_config.get("ram_threshold", 85.0),
            disk_percent=monitor_config.get("disk_threshold", 90.0),
            temperature_celsius=monitor_config.get("temp_threshold", 80.0)
        )
        self.system_monitor = SystemMonitor(
            thresholds=thresholds,
            check_interval=monitor_config.get("check_interval", 30.0),
            on_alert=self._queue_alert
        )
        self.system_query_handler = SystemQueryHandler(self.system_monitor)

        # Initialize system control
        control_config = self.config.get("control", {})
        self.system_control = SystemControl(
            log_file=control_config.get("log_file", "logs/actions.log")
        )
        self.control_handler = ControlQueryHandler(self.system_control)

        # Initialize reminders
        reminder_config = self.config.get("reminders", {})
        self.reminder_manager = ReminderManager(
            db_path=reminder_config.get("db_path", "memory/reminders.db"),
            on_reminder=self._queue_alert,
            check_interval=reminder_config.get("check_interval", 30.0),
            work_break_interval=reminder_config.get("work_break_interval", 60)
        )
        self.reminder_handler = ReminderQueryHandler(self.reminder_manager)

        # Initialize calendar
        calendar_config = self.config.get("calendar", {})
        self.calendar_manager = CalendarManager(
            ics_paths=calendar_config.get("ics_paths"),
            reminder_minutes=calendar_config.get("reminder_minutes", [15, 5])
        )
        self.calendar_manager.set_reminder_callback(self._queue_alert)
        self.calendar_handler = CalendarQueryHandler(self.calendar_manager)

        # Initialize dev tools
        dev_config = self.config.get("dev_tools", {})
        self.dev_tools = DevToolsManager(
            working_dir=dev_config.get("working_dir")
        )
        self.dev_handler = DevQueryHandler(self.dev_tools)

        # Initialize screen vision
        claude_config = self.config.get("claude", {})
        self.screen_analyzer = ScreenAnalyzer(
            claude_command=claude_config.get("command", "claude")
        )
        self.screen_handler = ScreenQueryHandler(self.screen_analyzer)

        # Initialize camera vision
        camera_config = self.config.get("camera_vision", {})
        self.camera_analyzer = CameraAnalyzer(
            claude_command=claude_config.get("command", "claude"),
            device=camera_config.get("device")
        )
        self.camera_handler = CameraQueryHandler(self.camera_analyzer)

        # Initialize input control
        input_config = self.config.get("input_control", {})
        self.input_controller = SafeInputController(
            demo_mode=input_config.get("demo_mode", False)
        )
        self.input_handler = InputQueryHandler(self.input_controller)

        # Initialize visual automation
        self.visual_automation = VisualAutomation(
            screen_analyzer=self.screen_analyzer,
            input_controller=self.input_controller
        )
        self.automation_handler = VisualAutomationHandler(self.visual_automation)

        # Initialize memory system
        memory_config = self.config.get("memory", {})
        self.memory = get_memory(memory_config.get("db_path", "memory/jarvis_memory.db"))
        self.memory_handler = MemoryHandler(self.memory)

        # Initialize personality (load user name from memory if available)
        personality_config = self.config.get("personality", {})
        stored_user_name = self.memory.get_user_name()
        user_name = stored_user_name or personality_config.get("user_name")

        self.personality = JarvisPersonality(
            user_name=user_name,
            formality_level=personality_config.get("formality_level", "formal")
        )

        # Initialize modules
        self._init_modules()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info("JARVIS initialized")

    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_path}, using defaults")
            return self._default_config()

        with open(config_file, 'r') as f:
            return yaml.safe_load(f)

    def _default_config(self) -> dict:
        """Return default configuration."""
        return {
            "audio": {"sample_rate": 16000},
            "wake_word": {
                "model": "hey_jarvis",
                "threshold": 0.5,
                "fallback_model": "alexa"
            },
            "stt": {
                "model_path": "models/vosk-model-small-es-0.42",
                "silence_timeout": 2.0,
                "max_recording_time": 30.0
            },
            "tts": {
                "model_path": "models/es_ES-davefx-medium.onnx",
                "speed": 1.0
            },
            "claude": {
                "command": "claude",
                "timeout": 60
            },
            "behavior": {
                "allow_barge_in": True,
                "shutdown_phrase": "apágate",
                "wake_confirmation": "A sus órdenes"
            }
        }

    def _init_modules(self):
        """Initialize all modules."""
        sample_rate = self.config["audio"]["sample_rate"]

        # Wake word detector
        ww_config = self.config["wake_word"]
        self.wake_word = WakeWordDetector(
            model_name=ww_config["model"],
            threshold=ww_config["threshold"],
            sample_rate=sample_rate,
            fallback_model=ww_config["fallback_model"]
        )

        # Speech-to-Text
        stt_config = self.config["stt"]
        self.stt = SpeechToText(
            model_path=stt_config["model_path"],
            sample_rate=sample_rate,
            silence_timeout=stt_config["silence_timeout"],
            max_recording_time=stt_config["max_recording_time"]
        )

        # Text-to-Speech
        tts_config = self.config["tts"]
        self.tts = TextToSpeech(
            model_path=tts_config["model_path"],
            speed=tts_config.get("speed", 1.0)
        )

        # Claude CLI bridge with JARVIS personality
        claude_config = self.config["claude"]
        self.claude = ClaudeBridge(
            command=claude_config["command"],
            timeout=claude_config["timeout"],
            system_prompt=self.personality.get_system_prompt()
        )

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info("Shutdown signal received")
        self.shutdown()

    def _queue_alert(self, message: str) -> None:
        """Queue an alert for delivery."""
        self._pending_alerts.append(message)
        logger.info(f"Alert queued: {message}")

    def _deliver_pending_alerts(self) -> None:
        """Deliver any pending system alerts."""
        while self._pending_alerts:
            alert = self._pending_alerts.pop(0)
            self._speak(alert)

    def run(self):
        """Main run loop."""
        self.running = True
        logger.info("JARVIS starting...")

        # Start memory session
        self.memory_handler.start_session()

        # Start system monitoring
        self.system_monitor.start_monitoring()

        # Start reminder and calendar monitoring
        self.reminder_manager.start()
        self.calendar_manager.start_monitoring()

        # Startup greeting with personality (includes today's agenda)
        startup_message = self.personality.get_startup_message()
        self._speak(startup_message)

        while self.running and not self._shutdown_requested:
            try:
                # Wait for wake word
                logger.info("Waiting for wake word...")
                self.wake_word.listen_once(timeout=None)

                if not self.running:
                    break

                # Handle interaction
                self._handle_interaction()

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                continue

        logger.info("JARVIS shutting down...")

        # Stop system monitoring
        self.system_monitor.stop_monitoring()

        # Stop reminder and calendar monitoring
        self.reminder_manager.stop()
        self.calendar_manager.stop_monitoring()

        # End memory session
        self.memory_handler.end_session()

        shutdown_message = self.personality.get_shutdown_message()
        self._speak(shutdown_message)

    def _handle_interaction(self):
        """Handle a single interaction after wake word detection."""
        self._interrupt_requested = False

        # Deliver any pending system alerts first
        self._deliver_pending_alerts()

        # Wake word confirmation with personality
        wake_response = self.personality.get_wake_response()
        self._speak(wake_response)

        # Listen for command
        logger.info("Listening for command...")

        # Setup barge-in if enabled
        if self.config["behavior"]["allow_barge_in"]:
            barge_in_thread = threading.Thread(
                target=self._barge_in_listener,
                daemon=True
            )
            barge_in_thread.start()

        user_input = self.stt.listen(
            on_partial=lambda text: logger.debug(f"Partial: {text}"),
            interrupt_check=lambda: self._interrupt_requested
        )

        if not user_input:
            logger.info("No input received")
            return

        logger.info(f"User said: {user_input}")

        # Check for shutdown command
        shutdown_phrase = self.config["behavior"]["shutdown_phrase"]
        if shutdown_phrase.lower() in user_input.lower():
            logger.info("Shutdown command received")
            self._shutdown_requested = True
            self.running = False
            return

        # Store user input in memory
        self.memory_handler.add_to_history("user", user_input)

        # Check for memory commands first (recuerda que..., olvida..., etc.)
        is_memory_cmd, memory_response = self.memory_handler.process_input(user_input)
        if is_memory_cmd and memory_response:
            logger.info("Memory command processed")
            # Update personality with new user name if learned
            new_name = self.memory.get_user_name()
            if new_name and new_name != self.personality.user_name:
                self.personality.set_user_name(new_name)
            self.memory_handler.add_to_history("assistant", memory_response)
            self._speak(memory_response)
            return

        # Check for system queries (cómo está el sistema, RAM, CPU, etc.)
        is_system_query, system_response = self.system_query_handler.process_query(user_input)
        if is_system_query and system_response:
            logger.info("System query processed")
            self.memory_handler.add_to_history("assistant", system_response)
            self._speak(system_response)
            return

        # Check for control commands (abre, cierra, volumen, brillo, etc.)
        is_control_cmd, control_response = self.control_handler.process_command(user_input)
        if is_control_cmd and control_response:
            logger.info("Control command processed")
            self.memory_handler.add_to_history("assistant", control_response)
            self._speak(control_response)
            return

        # Check for reminder commands (recuérdame, notas, etc.)
        is_reminder_cmd, reminder_response = self.reminder_handler.process_input(user_input)
        if is_reminder_cmd and reminder_response:
            logger.info("Reminder command processed")
            self.memory_handler.add_to_history("assistant", reminder_response)
            self._speak(reminder_response)
            return

        # Check for calendar queries (agenda, reuniones, etc.)
        is_calendar_query, calendar_response = self.calendar_handler.process_query(user_input)
        if is_calendar_query and calendar_response:
            logger.info("Calendar query processed")
            self.memory_handler.add_to_history("assistant", calendar_response)
            self._speak(calendar_response)
            return

        # Check for dev queries (git, docker, tests, files)
        is_dev_query, dev_response = self.dev_handler.process_query(user_input)
        if is_dev_query and dev_response:
            logger.info("Dev query processed")
            self.memory_handler.add_to_history("assistant", dev_response)
            self._speak(dev_response)
            return

        # Check for screen queries (qué hay en pantalla, errores, texto)
        is_screen_query, _ = self.screen_handler.process_query(user_input)
        if is_screen_query:
            logger.info("Screen query detected")
            # Notify user before capture
            self._speak("Capturando pantalla, un momento.")
            _, screen_response = self.screen_handler.process_query(user_input)
            if screen_response:
                self.memory_handler.add_to_history("assistant", screen_response)
                self._speak(screen_response)
            return

        # Check for camera queries (qué ves, hay alguien, cómo me veo)
        is_camera_query, _ = self.camera_handler.process_query(user_input)
        if is_camera_query:
            logger.info("Camera query detected")
            # Privacy notice before capture
            self._speak("Señor, activando cámara.")
            _, camera_response = self.camera_handler.process_query(user_input)
            if camera_response:
                self.memory_handler.add_to_history("assistant", camera_response)
                self._speak(camera_response)
            return

        # Check for input control commands (mouse, teclado, clicks)
        is_input_cmd, input_response = self.input_handler.process_query(user_input)
        if is_input_cmd and input_response:
            logger.info("Input control command processed")
            self.memory_handler.add_to_history("assistant", input_response)
            self._speak(input_response)
            return

        # Check for visual automation tasks (tareas complejas multi-paso)
        is_automation, automation_response = self.automation_handler.process_query(user_input)
        if is_automation and automation_response:
            logger.info("Visual automation task processed")
            self.memory_handler.add_to_history("assistant", automation_response)
            self._speak(automation_response)
            return

        # Track conversation
        self.personality.increment_conversation()

        # Build context with memory
        memory_context = self.memory_handler.get_context_for_prompt()
        conversation_context = self.conversation.get_context()

        full_context = ""
        if memory_context:
            full_context = f"## Información del usuario:\n{memory_context}\n\n"
        if conversation_context:
            full_context += f"## Conversación reciente:\n{conversation_context}"

        # Send to Claude
        logger.info("Processing with Claude...")
        response = self.claude.send_with_context(
            user_input,
            context=full_context if full_context else None
        )

        if response:
            # Store in conversation history (both in-memory and persistent)
            self.conversation.add_exchange(user_input, response)
            self.memory_handler.add_to_history("assistant", response)

            # Speak response (with barge-in support)
            self._speak_with_barge_in(response)
        else:
            # Use personality for error message
            error_msg = self.personality.get_limitation_message()
            self.memory_handler.add_to_history("assistant", error_msg)
            self._speak(error_msg)

    def _speak(self, text: str):
        """Speak text."""
        logger.info(f"Speaking: {text[:50]}...")
        self.tts.speak(text, blocking=True)

    def _speak_with_barge_in(self, text: str):
        """Speak with barge-in support."""
        if not self.config["behavior"]["allow_barge_in"]:
            self._speak(text)
            return

        # Start speaking non-blocking
        self.tts.speak(text, blocking=False)

        # Listen for wake word during speech
        def on_barge_in():
            logger.info("Barge-in detected!")
            self.tts.stop()
            self._interrupt_requested = True

        # Run wake word detection while speaking
        barge_in_thread = threading.Thread(
            target=lambda: self.wake_word.listen(
                on_detection=on_barge_in,
                interrupt_check=lambda: not self.tts.is_speaking
            ),
            daemon=True
        )
        barge_in_thread.start()

        # Wait for speech to complete
        self.tts.wait()

        # Stop barge-in listener
        self.wake_word.stop()

        # If interrupted, handle new interaction
        if self._interrupt_requested:
            self._handle_interaction()

    def _barge_in_listener(self):
        """Background listener for barge-in during STT."""
        # This runs during STT to detect if user says wake word
        # to interrupt and restart
        pass

    def shutdown(self):
        """Shutdown JARVIS."""
        self.running = False
        self._shutdown_requested = True
        self.system_monitor.stop_monitoring()
        self.reminder_manager.stop()
        self.calendar_manager.stop_monitoring()
        self.wake_word.stop()
        self.stt.stop()
        self.tts.stop()


def main():
    """Entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="JARVIS Voice Assistant")
    parser.add_argument(
        "-c", "--config",
        default="config.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        jarvis = Jarvis(config_path=args.config)
        jarvis.run()
    except FileNotFoundError as e:
        logger.error(f"Missing required file: {e}")
        logger.error("Run install_phase1.sh to download models")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
