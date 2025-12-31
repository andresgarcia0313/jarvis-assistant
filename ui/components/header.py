"""
HeaderComponent - Título y estado de JARVIS.

Componente autocontenido con estilos inline.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QApplication
from PyQt5.QtCore import Qt
from .theme import CYAN, BG, TEXT_DIM, GREEN


class HeaderComponent(QWidget):
    """Header: título + config + estado."""

    # Estilos locales
    STYLE_TITLE = f"font-size:28px;font-weight:700;color:{CYAN};letter-spacing:6px;"
    STYLE_BTN = f"background:{BG};color:{CYAN};border:1px solid {CYAN};padding:8px 16px;font-weight:600;"
    STYLE_STATUS_OFF = f"color:{TEXT_DIM};background:{BG};padding:4px 12px;border-radius:12px;border:1px solid {TEXT_DIM};"
    STYLE_STATUS_ON = f"color:{GREEN};background:{GREEN}20;padding:4px 12px;border-radius:12px;border:1px solid {GREEN};"

    def __init__(self, on_config=None):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Título
        title = QLabel("J.A.R.V.I.S.")
        title.setStyleSheet(self.STYLE_TITLE)
        layout.addWidget(title)
        layout.addStretch()

        # Config
        self.config_btn = QPushButton("CONFIG")
        self.config_btn.setStyleSheet(self.STYLE_BTN)
        self.config_btn.setCursor(Qt.PointingHandCursor)
        if on_config:
            self.config_btn.clicked.connect(on_config)
        layout.addWidget(self.config_btn)

        # Status
        self._status = QLabel("STANDBY")
        self._status.setStyleSheet(self.STYLE_STATUS_OFF)
        layout.addWidget(self._status)

    def set_status(self, text: str, active: bool = False):
        self._status.setText(text)
        self._status.setStyleSheet(self.STYLE_STATUS_ON if active else self.STYLE_STATUS_OFF)

    def set_status_custom(self, text: str, style: str):
        self._status.setText(text)
        self._status.setStyleSheet(style)


# Test independiente
if __name__ == "__main__":
    app = QApplication([])
    w = HeaderComponent(on_config=lambda: print("Config clicked"))
    w.setStyleSheet(f"background:{BG};")
    w.show()
    app.exec_()
