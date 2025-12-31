"""
ControlsComponent - Botones de control principales.

Componente autocontenido con estilos inline.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QApplication
from PyQt5.QtCore import Qt
from .theme import CYAN, BG, BORDER, RED


class ControlsComponent(QWidget):
    """Barra de controles: Activate + Clear."""

    STYLE_PRIMARY = f"""
        QPushButton {{
            background:{BG};color:{CYAN};border:2px solid {CYAN};
            font-size:14px;font-weight:700;letter-spacing:2px;border-radius:6px;
        }}
        QPushButton:hover {{background:{CYAN}20;}}
    """
    STYLE_RECORDING = f"""
        QPushButton {{
            background:{RED}30;color:{RED};border:2px solid {RED};
            font-size:14px;font-weight:700;letter-spacing:2px;border-radius:6px;
        }}
        QPushButton:hover {{background:{RED}50;}}
    """
    STYLE_SECONDARY = f"""
        QPushButton {{
            background:{BG};color:{BORDER};border:1px solid {BORDER};
            font-size:12px;font-weight:600;letter-spacing:1px;border-radius:6px;
        }}
        QPushButton:hover {{background:{BORDER}30;}}
    """

    def __init__(self, on_toggle=None, on_clear=None):
        super().__init__()
        self._active = False
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self._toggle = QPushButton("ACTIVATE")
        self._toggle.setMinimumHeight(54)
        self._toggle.setStyleSheet(self.STYLE_PRIMARY)
        self._toggle.setCursor(Qt.PointingHandCursor)
        if on_toggle:
            self._toggle.clicked.connect(on_toggle)
        layout.addWidget(self._toggle, 2)

        clear = QPushButton("CLEAR")
        clear.setMinimumHeight(54)
        clear.setStyleSheet(self.STYLE_SECONDARY)
        clear.setCursor(Qt.PointingHandCursor)
        if on_clear:
            clear.clicked.connect(on_clear)
        layout.addWidget(clear, 1)

    def set_active(self, active: bool):
        self._active = active
        self._toggle.setText("DEACTIVATE" if active else "ACTIVATE")
        self._toggle.setStyleSheet(self.STYLE_RECORDING if active else self.STYLE_PRIMARY)

    def is_active(self) -> bool:
        return self._active


if __name__ == "__main__":
    app = QApplication([])
    w = ControlsComponent(
        on_toggle=lambda: print("Toggle"),
        on_clear=lambda: print("Clear")
    )
    w.setStyleSheet(f"background:{BG};")
    w.show()
    app.exec_()
