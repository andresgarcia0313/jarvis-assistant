"""
JARVIS HUD GUI - Interfaz estilo Iron Man con diagnóstico de inicio.

Arquitectura de componentes modulares para facilitar mantenimiento y testing.
"""

import sys
import signal
from pathlib import Path
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QStackedWidget
from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QThread

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import yaml
from ui.hud_style import MAIN_STYLE, COLORS, get_status_style, get_audio_level_color
from ui.listener_factory import create_listener_from_config
from ui.jarvis_brain import JarvisBrain
from ui.config_dialog import ConfigDialog
from ui.tts_engine import TTSEngine
from ui.diagnostics import SystemDiagnostics, DiagnosticResult
from ui.logger_config import get_logger, log_ui, log_stt, log_tts, log_brain, log_audio
from ui.components import DiagnosticsScreen, MainScreen

logger = get_logger(__name__)
RESPONSES_FILE = PROJECT_ROOT / "respuestas_jarvis.md"
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"

# Variable global para la instancia del HUD (para manejo de señales)
_hud_instance = None


class SignalBridge(QObject):
    user_text = pyqtSignal(str, bool)
    jarvis_response = pyqtSignal(str)
    jarvis_error = pyqtSignal(str)
    log_event = pyqtSignal(str, str)
    tts_finished = pyqtSignal()
    screenshot_requested = pyqtSignal(str)  # nombre de la captura
    diag_result = pyqtSignal(object)  # DiagnosticResult
    diag_complete = pyqtSignal(bool)  # True si todo OK


class DiagnosticsThread(QThread):
    """Thread para ejecutar diagnósticos sin bloquear UI."""
    result_ready = pyqtSignal(object)  # DiagnosticResult
    finished_signal = pyqtSignal(bool)

    def __init__(self, model_path: str):
        super().__init__()
        self.model_path = model_path

    def run(self):
        diag = SystemDiagnostics(self.model_path)
        diag.set_progress_callback(lambda r: self.result_ready.emit(r))
        success = diag.run_all()
        self.finished_signal.emit(success)


class JarvisHUD(QWidget):
    WAKE_WORDS = ["jarvis", "jarvi", "jarby", "harvey", "chavis", "chaves"]

    def __init__(self, model_path: str, test_mode: bool = False):
        super().__init__()
        global _hud_instance
        _hud_instance = self

        logger.info("Inicializando JARVIS HUD")
        self.model_path = model_path
        self.test_mode = test_mode
        self._screenshot_counter = 0
        self._diag_passed = False
        self.signals = SignalBridge()
        self._pending_command = ""
        self._config = {"mode": "repl", "api_key": "", "tts_enabled": True}
        self._log_collapsed = False

        # Configurar UI y estilo
        self.setStyleSheet(MAIN_STYLE)
        self._setup_signals()
        self._setup_screenshot_handler()
        self._setup_window()

        # Iniciar con pantalla de diagnóstico
        self._run_diagnostics()

    def _setup_window(self):
        """Configura la ventana principal con stack de pantallas."""
        self.setWindowTitle("J.A.R.V.I.S.")
        self.setMinimumSize(850, 750)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Stack para alternar entre diagnóstico y UI principal
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # Página 0: Pantalla de diagnóstico
        self._setup_diag_ui()

        # Página 1: UI principal (se configura después del diagnóstico)

    def _setup_diag_ui(self):
        """Crea la pantalla de diagnóstico usando el componente modular."""
        self.diag_screen = DiagnosticsScreen(on_continue=self._on_diag_continue)
        self.stack.addWidget(self.diag_screen)

    def _run_diagnostics(self):
        """Ejecuta los diagnósticos en un thread separado."""
        logger.info("Iniciando diagnósticos del sistema")

        self.diag_thread = DiagnosticsThread(self.model_path)
        self.diag_thread.result_ready.connect(self._on_diag_result)
        self.diag_thread.finished_signal.connect(self._on_diag_finished)
        self.diag_thread.start()

    def _on_diag_result(self, result: DiagnosticResult):
        """Callback cuando se completa un diagnóstico individual."""
        self.diag_screen.add_result(result.name, result.status, result.message)

    def _on_diag_finished(self, success: bool):
        """Callback cuando todos los diagnósticos terminan."""
        self._diag_passed = success
        self.diag_screen.set_complete(success)
        log_ui(action="diagnostics_complete", success=success)

        # En modo test, capturar diagnóstico y continuar automáticamente
        if self.test_mode:
            QTimer.singleShot(300, lambda: self.capture_screenshot("diagnostico"))
            QTimer.singleShot(1500, self._on_diag_continue)

    def _on_diag_continue(self):
        """Continúa a la interfaz principal después del diagnóstico."""
        logger.info("Diagnóstico completado, iniciando interfaz principal")

        # Cargar configuración
        config_path = PROJECT_ROOT / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Inicializar componentes de audio/voz usando factory
        self.listener = create_listener_from_config(config)
        self.brain = JarvisBrain()
        self.tts = TTSEngine()
        self._init_responses_file()
        self._setup_audio_monitor()

        # Crear la UI principal
        self._setup_main_ui()

        # Cambiar a la pantalla principal
        self.stack.setCurrentIndex(1)

        self._log("Sistema JARVIS en línea", "ok")
        log_ui(action="startup", status="ok")

        if self.test_mode:
            QTimer.singleShot(500, lambda: self.capture_screenshot("inicio"))
        else:
            self.tts.speak("Todos los sistemas operativos. A su servicio, señor.")

    def _init_responses_file(self):
        if not RESPONSES_FILE.exists():
            RESPONSES_FILE.write_text("# Historial JARVIS\n\n")

    def _setup_signals(self):
        self.signals.user_text.connect(self._on_user_text)
        self.signals.jarvis_response.connect(self._on_jarvis_response)
        self.signals.jarvis_error.connect(self._on_jarvis_error)
        self.signals.log_event.connect(self._on_log_event)
        self.signals.tts_finished.connect(self._on_tts_finished)
        self.signals.screenshot_requested.connect(self.capture_screenshot)

    def _setup_screenshot_handler(self):
        """Configura el manejador de señal SIGUSR1 para capturas de pantalla."""
        def handler(signum, frame):
            # Emitir señal Qt desde el manejador Unix
            if _hud_instance:
                _hud_instance.signals.screenshot_requested.emit("signal")
        signal.signal(signal.SIGUSR1, handler)
        logger.info("Manejador de señales configurado (SIGUSR1 para capturas)")

    def capture_screenshot(self, name: str = "screenshot") -> str:
        """Captura la ventana actual usando PyQt5 (independiente del SO)."""
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

        self._screenshot_counter += 1
        ts = datetime.now().strftime("%H%M%S")
        filename = f"{ts}_{self._screenshot_counter:02d}_{name}.png"
        filepath = SCREENSHOTS_DIR / filename

        try:
            # Capturar usando PyQt5 - método multiplataforma
            pixmap = self.grab()
            saved = pixmap.save(str(filepath), "PNG")

            if saved and filepath.exists():
                self._log(f"Captura guardada: {filename}", "info")
                log_ui(action="screenshot", filename=filename, size=filepath.stat().st_size)
                logger.info(f"Screenshot guardado: {filepath}")
                return str(filepath)
            else:
                self._log(f"Error guardando captura", "error")
                logger.error(f"No se pudo guardar screenshot: {filepath}")
                return ""
        except Exception as e:
            self._log(f"Error en captura: {e}", "error")
            logger.error(f"Error capturando screenshot: {e}")
            return ""

    def _setup_audio_monitor(self):
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self._update_audio_level)

    def _log(self, msg: str, tipo: str = "info"):
        self.signals.log_event.emit(msg, tipo)

    def _setup_main_ui(self):
        """Configura la UI principal usando el componente modular MainScreen."""
        self.main_screen = MainScreen(
            on_config=self._open_config,
            on_toggle=self._toggle,
            on_clear=self._clear
        )
        self.stack.addWidget(self.main_screen)
        logger.info("UI principal inicializada correctamente")

    def _toggle_log(self):
        """Muestra/oculta el panel de log (delegado al componente)."""
        # El toggle está manejado internamente por SystemLogPanel
        log_ui(action="toggle_log")

    def _open_config(self):
        log_ui(action="open_config")
        dialog = ConfigDialog(
            self,
            self._config.get("mode", "repl"),
            self._config.get("api_key", ""),
            self._config.get("device"),
            self._config.get("tts_enabled", True)
        )
        if dialog.exec_():
            old_device = self._config.get("device")
            self._config = dialog.get_config()
            new_device = self._config.get("device")

            if old_device != new_device:
                was_running = self.listener.is_running()
                if was_running:
                    self._stop()
                self.listener.set_device(new_device)
                if was_running:
                    self._start()
                self._log(f"Micrófono actualizado", "config")
                log_audio(action="device_changed", device=new_device)

            self._log(f"Config: modo {self._config['mode'].upper()}", "config")
            log_ui(action="config_saved", mode=self._config['mode'])

    def _toggle(self):
        if self.listener.is_running():
            self._stop()
        else:
            self._start()

    def _start(self):
        self._log("Initializing audio input...", "info")
        log_audio(action="start_listening")

        self.listener.start(self._on_text_thread)
        self.audio_timer.start(100)

        self.main_screen.set_active(True)
        self.main_screen.set_status("LISTENING", active=True)

        self._log("Voice interface active - Say 'JARVIS' + command", "ok")
        log_audio(action="listening_started")

    def _stop(self):
        self.listener.stop()
        self.audio_timer.stop()
        self.main_screen.reset_audio()

        self.main_screen.set_active(False)
        self.main_screen.set_status("STANDBY", active=False)

        self._log("Voice interface deactivated", "info")
        log_audio(action="listening_stopped")

    def _clear(self):
        self.main_screen.clear_all()
        self._log("Display cleared", "info")
        log_ui(action="screen_cleared")

    def _update_audio_level(self):
        if self.listener.is_running():
            level = min(100, self.listener.get_audio_level())
            self.main_screen.set_audio_level(level)

    def _on_text_thread(self, text: str, is_final: bool):
        self.signals.user_text.emit(text, is_final)

    def _contains_wake_word(self, text: str) -> bool:
        return any(w in text.lower() for w in self.WAKE_WORDS)

    def _extract_command(self, text: str) -> str:
        t = text.lower()
        for w in self.WAKE_WORDS:
            if w in t:
                return text[t.find(w) + len(w):].strip(" ,.")
        return text

    def _on_user_text(self, text: str, is_final: bool):
        log_stt(action="text_received", text=text[:50], is_final=is_final)

        # Barge-in: interrumpir TTS si el usuario dice Jarvis mientras habla
        if self.tts.is_speaking() and self._contains_wake_word(text):
            self.tts.stop()
            self._log("Interrumpido por usuario", "info")
            log_tts(action="interrupted")

        if is_final:
            self.main_screen.append_voice_input(text)
            self._log(f'Escuché: "{text}"', "hear")
            log_stt(action="final_text", text=text)

            if self._contains_wake_word(text):
                cmd = self._extract_command(text)
                if cmd:
                    self._log(f'Wake word detectado - Comando: "{cmd}"', "wake")
                    log_stt(action="wake_word_detected", command=cmd)
                    self._process_command(cmd)
                else:
                    self.main_screen.append_response("A sus órdenes, señor. ¿Qué necesita?")
                    self.tts.speak("A sus órdenes, señor. ¿Qué necesita?")
                    self._log("Wake word sin comando", "warn")
                    log_stt(action="wake_word_no_command")
        else:
            # Texto parcial en status
            display_text = text[-40:] if len(text) > 40 else text
            self.main_screen.set_status(display_text)

            # Fallback: wake word en parcial largo
            if len(text) > 15 and self._contains_wake_word(text):
                cmd = self._extract_command(text)
                if cmd and len(cmd) > 5 and not self._pending_command:
                    self._log(f'Wake word parcial: "{text}"', "wake")
                    self.main_screen.append_voice_input(text)
                    self._process_command(cmd)

    def _process_command(self, text: str):
        self._pending_command = text
        self.main_screen.set_status_custom(
            "Procesando...",
            f"color: {COLORS['warning']}; background-color: {COLORS['warning']}20; padding: 4px 12px; border-radius: 12px;"
        )

        mode = self._config["mode"].upper()
        self._log(f'Enviando a IA ({mode}): "{text}"', "send")
        log_brain(action="request_sent", text=text[:50], mode=mode)

        self.main_screen.append_response(f'\nProcesando: "{text}"\n')

        self.brain.process(
            text,
            on_response=lambda r: self.signals.jarvis_response.emit(r),
            on_error=lambda e: self.signals.jarvis_error.emit(e)
        )

    def _on_log_event(self, msg: str, tipo: str):
        ts = datetime.now().strftime("%H:%M:%S")
        icons = {
            "info": "i", "ok": "+", "warn": "!", "error": "x",
            "hear": ">", "wake": "*", "send": "^", "recv": "v", "config": "#"
        }
        icon = icons.get(tipo, "-")
        # Solo escribir si main_screen existe (no durante diagnóstico)
        if hasattr(self, 'main_screen') and self.main_screen:
            self.main_screen.append_log(f"[{ts}] [{icon}] {msg}")

    def _save_to_file(self, user_text: str, response: str):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(RESPONSES_FILE, "a", encoding="utf-8") as f:
            f.write(f"\n## {ts}\n\n**Usuario:** {user_text}\n\n**JARVIS:** {response}\n\n---\n")

    def _on_jarvis_response(self, response: str):
        self.main_screen.append_response(f"{response}\n")
        self._log(f"Respuesta recibida ({len(response)} chars)", "recv")
        log_brain(action="response_received", length=len(response))

        self._save_to_file(self._pending_command, response)
        self._pending_command = ""

        if self._config.get("tts_enabled", True):
            self.main_screen.set_status_custom(
                "Hablando...",
                f"color: {COLORS['accent']}; background-color: {COLORS['accent']}20; padding: 4px 12px; border-radius: 12px;"
            )
            self._log("Reproduciendo respuesta...", "info")
            log_tts(action="speaking_started")
            self.tts.speak(response, on_complete=lambda: self.signals.tts_finished.emit())
        else:
            self._set_listening_status()

    def _on_tts_finished(self):
        self._set_listening_status()
        self._log("Listo para escuchar", "ok")
        log_tts(action="speaking_finished")

    def _set_listening_status(self):
        if self.listener.is_running():
            self.main_screen.set_status("Escuchando", active=True)
        else:
            self.main_screen.set_status("Inactivo", active=False)

    def _on_jarvis_error(self, error: str):
        self.main_screen.append_response(f"Error: {error}\n")
        self._set_listening_status()
        self._log(f"Error: {error}", "error")
        log_brain(action="error", error=error)
        self._pending_command = ""

    def closeEvent(self, event):
        logger.info("Cerrando JARVIS HUD")
        log_ui(action="shutdown")
        self.tts.stop()
        self.listener.stop()
        self.audio_timer.stop()
        event.accept()
