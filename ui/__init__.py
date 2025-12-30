"""
JARVIS UI Module
Provides visual feedback through a minimalist status widget.
"""

import logging
import threading
import time
from typing import Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

# Check if PyQt/PySide is available
try:
    from PyQt5.QtWidgets import (
        QApplication, QWidget, QLabel, QVBoxLayout,
        QHBoxLayout, QSystemTrayIcon, QMenu
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QIcon, QColor, QPalette, QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False
    logger.info("PyQt5 not available, widget disabled")


class JarvisState(Enum):
    """JARVIS operational states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"
    ERROR = "error"


@dataclass
class StatusUpdate:
    """A status update for the widget."""
    state: JarvisState
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class WidgetController:
    """Controller for the status widget (works without Qt)."""

    def __init__(self, max_history: int = 5):
        self.state = JarvisState.IDLE
        self.message = ""
        self.command_history: List[str] = []
        self.max_history = max_history
        self.callbacks: List[Callable] = []

    def set_state(self, state: JarvisState, message: str = ""):
        """Update the current state."""
        self.state = state
        self.message = message
        self._notify()

    def add_command(self, command: str):
        """Add a command to history."""
        self.command_history.insert(0, command)
        if len(self.command_history) > self.max_history:
            self.command_history.pop()
        self._notify()

    def add_callback(self, callback: Callable):
        """Add a callback for state changes."""
        self.callbacks.append(callback)

    def _notify(self):
        """Notify all callbacks of state change."""
        for callback in self.callbacks:
            try:
                callback(self.state, self.message)
            except Exception as e:
                logger.error(f"Callback error: {e}")

    def get_state_text(self) -> str:
        """Get human-readable state text."""
        state_texts = {
            JarvisState.IDLE: "En reposo",
            JarvisState.LISTENING: "Escuchando...",
            JarvisState.PROCESSING: "Procesando...",
            JarvisState.SPEAKING: "Hablando...",
            JarvisState.ERROR: "Error",
        }
        return state_texts.get(self.state, "Desconocido")

    def get_status_summary(self) -> str:
        """Get a text summary of current status."""
        summary = f"Estado: {self.get_state_text()}"
        if self.message:
            summary += f"\n{self.message}"
        if self.command_history:
            summary += f"\nÚltimo comando: {self.command_history[0]}"
        return summary


if HAS_QT:
    class StatusWidget(QWidget):
        """Minimalist status widget for JARVIS."""

        # Colors for different states
        STATE_COLORS = {
            JarvisState.IDLE: "#2d2d2d",
            JarvisState.LISTENING: "#1a5f7a",
            JarvisState.PROCESSING: "#4a4a4a",
            JarvisState.SPEAKING: "#2d4a2d",
            JarvisState.ERROR: "#5f1a1a",
        }

        def __init__(self, controller: WidgetController):
            super().__init__()
            self.controller = controller
            self.controller.add_callback(self._on_state_change)

            self._setup_ui()
            self._setup_tray()

        def _setup_ui(self):
            """Setup the widget UI."""
            self.setWindowTitle("JARVIS")
            self.setWindowFlags(
                Qt.WindowStaysOnTopHint |
                Qt.FramelessWindowHint |
                Qt.Tool
            )
            self.setAttribute(Qt.WA_TranslucentBackground)

            # Main layout
            layout = QVBoxLayout(self)
            layout.setContentsMargins(10, 10, 10, 10)

            # State indicator
            self.state_label = QLabel("JARVIS")
            self.state_label.setFont(QFont("Monospace", 12, QFont.Bold))
            self.state_label.setStyleSheet("color: #00ff00;")
            layout.addWidget(self.state_label)

            # Status message
            self.message_label = QLabel("En reposo")
            self.message_label.setFont(QFont("Monospace", 10))
            self.message_label.setStyleSheet("color: #aaaaaa;")
            layout.addWidget(self.message_label)

            # Last command
            self.command_label = QLabel("")
            self.command_label.setFont(QFont("Monospace", 9))
            self.command_label.setStyleSheet("color: #666666;")
            layout.addWidget(self.command_label)

            # Styling
            self.setStyleSheet("""
                QWidget {
                    background-color: rgba(30, 30, 30, 200);
                    border: 1px solid #444;
                    border-radius: 5px;
                }
            """)

            self.resize(250, 80)
            self._position_widget()

        def _position_widget(self):
            """Position widget in top-right corner."""
            try:
                screen = QApplication.primaryScreen().geometry()
                self.move(screen.width() - self.width() - 20, 20)
            except Exception:
                pass

        def _setup_tray(self):
            """Setup system tray icon."""
            try:
                self.tray = QSystemTrayIcon(self)
                menu = QMenu()
                menu.addAction("Mostrar", self.show)
                menu.addAction("Ocultar", self.hide)
                menu.addSeparator()
                menu.addAction("Salir", QApplication.quit)
                self.tray.setContextMenu(menu)
                self.tray.show()
            except Exception as e:
                logger.warning(f"Tray icon setup failed: {e}")

        def _on_state_change(self, state: JarvisState, message: str):
            """Handle state change from controller."""
            try:
                self.state_label.setText(f"JARVIS - {self.controller.get_state_text()}")

                if message:
                    self.message_label.setText(message[:50])
                else:
                    self.message_label.setText("")

                if self.controller.command_history:
                    cmd = self.controller.command_history[0]
                    self.command_label.setText(f"→ {cmd[:40]}")

                # Update background color
                color = self.STATE_COLORS.get(state, "#2d2d2d")
                self.setStyleSheet(f"""
                    QWidget {{
                        background-color: {color};
                        border: 1px solid #444;
                        border-radius: 5px;
                    }}
                """)

            except Exception as e:
                logger.error(f"Widget update error: {e}")

        def show_notification(self, title: str, message: str):
            """Show a notification."""
            if hasattr(self, 'tray') and self.tray:
                self.tray.showMessage(title, message)


class WidgetManager:
    """Manages the status widget in a separate thread."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and HAS_QT
        self.controller = WidgetController()
        self.widget: Optional['StatusWidget'] = None
        self._app: Optional['QApplication'] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self):
        """Start the widget in a separate thread."""
        if not self.enabled:
            logger.info("Widget disabled or Qt not available")
            return

        self._running = True
        self._thread = threading.Thread(target=self._run_widget, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the widget."""
        self._running = False
        if self._app:
            try:
                self._app.quit()
            except Exception:
                pass

    def _run_widget(self):
        """Run the Qt widget event loop."""
        try:
            import sys
            self._app = QApplication.instance() or QApplication(sys.argv)
            self.widget = StatusWidget(self.controller)
            self.widget.show()
            self._app.exec_()
        except Exception as e:
            logger.error(f"Widget error: {e}")

    def set_state(self, state: JarvisState, message: str = ""):
        """Update widget state."""
        self.controller.set_state(state, message)

    def add_command(self, command: str):
        """Add command to history."""
        self.controller.add_command(command)

    def show_notification(self, title: str, message: str):
        """Show a notification."""
        if self.widget:
            try:
                self.widget.show_notification(title, message)
            except Exception:
                pass


# Singleton instances
_widget_manager: Optional[WidgetManager] = None
_widget_controller: Optional[WidgetController] = None


def get_widget_controller() -> WidgetController:
    """Get or create the widget controller."""
    global _widget_controller

    if _widget_controller is None:
        _widget_controller = WidgetController()

    return _widget_controller


def get_widget_manager(enabled: bool = True) -> WidgetManager:
    """Get or create the widget manager."""
    global _widget_manager

    if _widget_manager is None:
        _widget_manager = WidgetManager(enabled)

    return _widget_manager
