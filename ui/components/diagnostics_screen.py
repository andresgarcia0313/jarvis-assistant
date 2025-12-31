"""
DiagnosticsScreen - Pantalla de diagnóstico de inicio.

Componente autocontenido con estilos inline.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QProgressBar, QPushButton, QApplication
)
from PyQt5.QtCore import Qt
from .theme import CYAN, BG, BORDER, TEXT_DIM, GREEN, YELLOW


class DiagnosticsScreen(QWidget):
    """Pantalla de diagnóstico de inicio de JARVIS."""

    STYLE_TITLE = f"font-size:48px;font-weight:700;color:{CYAN};letter-spacing:12px;padding:20px;"
    STYLE_SUB = f"font-size:14px;color:{TEXT_DIM};letter-spacing:3px;"
    STYLE_STATUS = f"font-size:12px;color:{CYAN};letter-spacing:2px;"
    STYLE_BAR = f"""
        QProgressBar {{border:none;background:{BORDER};border-radius:2px;}}
        QProgressBar::chunk {{background:{CYAN};border-radius:2px;}}
    """
    STYLE_BTN = f"""
        QPushButton {{
            background:{BG};color:{CYAN};border:2px solid {CYAN};
            font-size:14px;font-weight:700;letter-spacing:2px;padding:16px;border-radius:6px;
        }}
        QPushButton:hover {{background:{CYAN}20;}}
    """
    STYLE_OK = f"color:{GREEN};font-size:13px;padding:4px 0;"
    STYLE_WARN = f"color:{YELLOW};font-size:13px;padding:4px 0;"
    STYLE_ERR = f"color:#ff4444;font-size:13px;padding:4px 0;"

    def __init__(self, on_continue=None):
        super().__init__()
        self.setStyleSheet(f"background:{BG};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        title = QLabel("J.A.R.V.I.S.")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(self.STYLE_TITLE)
        layout.addWidget(title)

        sub = QLabel("Just A Rather Very Intelligent System")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(self.STYLE_SUB)
        layout.addWidget(sub)
        layout.addSpacing(30)

        self._status = QLabel("INICIANDO DIAGNÓSTICO DE SISTEMAS...")
        self._status.setAlignment(Qt.AlignCenter)
        self._status.setStyleSheet(self.STYLE_STATUS)
        layout.addWidget(self._status)

        self._bar = QProgressBar()
        self._bar.setRange(0, 6)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(4)
        self._bar.setStyleSheet(self.STYLE_BAR)
        layout.addWidget(self._bar)
        layout.addSpacing(20)

        self._results = QVBoxLayout()
        self._results.setSpacing(8)
        layout.addLayout(self._results)
        layout.addStretch()

        self._btn = QPushButton("INICIAR SISTEMA")
        self._btn.setStyleSheet(self.STYLE_BTN)
        self._btn.setVisible(False)
        if on_continue:
            self._btn.clicked.connect(on_continue)
        layout.addWidget(self._btn)

    def add_result(self, name: str, status: str, message: str):
        icons = {"ok": "[OK]", "warning": "[!]", "error": "[X]"}
        styles = {"ok": self.STYLE_OK, "warning": self.STYLE_WARN, "error": self.STYLE_ERR}
        item = QLabel(f"  {icons.get(status, '[-]')}  {name}: {message}")
        item.setStyleSheet(styles.get(status, self.STYLE_OK))
        self._results.addWidget(item)
        self._bar.setValue(self._bar.value() + 1)

    def set_complete(self, success: bool):
        if success:
            self._status.setText("TODOS LOS SISTEMAS OPERATIVOS")
            self._status.setStyleSheet(f"font-size:14px;color:{GREEN};letter-spacing:2px;font-weight:600;")
            self._btn.setText("INICIAR J.A.R.V.I.S.")
        else:
            self._status.setText("SE DETECTARON PROBLEMAS")
            self._status.setStyleSheet(f"font-size:14px;color:{YELLOW};letter-spacing:2px;font-weight:600;")
            self._btn.setText("CONTINUAR DE TODOS MODOS")
        self._btn.setVisible(True)


if __name__ == "__main__":
    app = QApplication([])
    w = DiagnosticsScreen(on_continue=lambda: print("Continue"))
    w.add_result("Modelo STT", "ok", "Vosk cargado")
    w.add_result("Motor TTS", "ok", "espeak-ng disponible")
    w.add_result("Claude CLI", "warning", "No encontrado")
    w.set_complete(False)
    w.resize(800, 600)
    w.show()
    app.exec_()
