"""
GUI Simple para JARVIS - Muestra transcripción en tiempo real.
"""

import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit, QLabel
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont

# Agregar path del proyecto
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ui.live_listener import LiveListener


class SignalBridge(QObject):
    """Bridge para signals entre threads."""
    text_received = pyqtSignal(str, bool)


class JarvisSimpleGUI(QWidget):
    """Ventana principal minimalista."""

    def __init__(self, model_path: str):
        super().__init__()
        self.listener = LiveListener(model_path)
        self.signals = SignalBridge()
        self.signals.text_received.connect(self._on_text)
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("JARVIS - Live")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Estado
        self.status_label = QLabel("APAGADO")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Monospace", 14, QFont.Bold))
        self.status_label.setStyleSheet("color: #888;")
        layout.addWidget(self.status_label)

        # Área de texto
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Monospace", 11))
        self.text_area.setStyleSheet("""
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #333;
            }
        """)
        layout.addWidget(self.text_area)

        # Botón ON/OFF
        self.toggle_btn = QPushButton("ENCENDER")
        self.toggle_btn.setFont(QFont("Monospace", 12, QFont.Bold))
        self.toggle_btn.setMinimumHeight(50)
        self.toggle_btn.clicked.connect(self._toggle)
        self._style_button(False)
        layout.addWidget(self.toggle_btn)

        # Estilo ventana
        self.setStyleSheet("background-color: #0a0a0a;")

    def _style_button(self, active: bool):
        if active:
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #8b0000;
                    color: white;
                    border: 2px solid #ff0000;
                }
                QPushButton:hover { background-color: #a00000; }
            """)
        else:
            self.toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #006400;
                    color: white;
                    border: 2px solid #00ff00;
                }
                QPushButton:hover { background-color: #008000; }
            """)

    def _toggle(self):
        if self.listener.is_running():
            self.listener.stop()
            self.toggle_btn.setText("ENCENDER")
            self.status_label.setText("APAGADO")
            self.status_label.setStyleSheet("color: #888;")
            self._style_button(False)
        else:
            self.listener.start(self._on_text_thread)
            self.toggle_btn.setText("APAGAR")
            self.status_label.setText("ESCUCHANDO...")
            self.status_label.setStyleSheet("color: #00ff00;")
            self._style_button(True)

    def _on_text_thread(self, text: str, is_final: bool):
        """Llamado desde thread del listener."""
        self.signals.text_received.emit(text, is_final)

    def _on_text(self, text: str, is_final: bool):
        """Actualiza UI con texto (en main thread)."""
        if is_final:
            self.text_area.append(f"► {text}")
        else:
            # Mostrar parcial en última línea
            cursor = self.text_area.textCursor()
            cursor.movePosition(cursor.End)
            self.text_area.setTextCursor(cursor)
            # Actualizar status con texto parcial
            self.status_label.setText(f"... {text[-50:]}")

    def closeEvent(self, event):
        self.listener.stop()
        event.accept()
