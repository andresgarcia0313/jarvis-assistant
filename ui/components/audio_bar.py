"""
AudioBarComponent - Barra de nivel de audio.

Componente autocontenido con estilos inline.
"""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QProgressBar, QApplication
from .theme import CYAN, BG, BORDER, TEXT_DIM, GREEN, YELLOW


class AudioBarComponent(QWidget):
    """Barra de nivel de audio con indicador visual."""

    STYLE_LABEL = f"color:{CYAN};font-size:11px;font-weight:600;letter-spacing:2px;"
    STYLE_BAR = f"""
        QProgressBar {{border:1px solid {BORDER};border-radius:5px;background:{BG};}}
        QProgressBar::chunk {{background:{CYAN};border-radius:4px;}}
    """

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        label = QLabel("AUDIO INPUT")
        label.setStyleSheet(self.STYLE_LABEL)
        layout.addWidget(label)

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(10)
        self._bar.setStyleSheet(self.STYLE_BAR)
        layout.addWidget(self._bar, 1)

        self._value = QLabel("0%")
        self._value.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;min-width:40px;")
        layout.addWidget(self._value)

    def set_level(self, level: int):
        level = max(0, min(100, level))
        self._bar.setValue(level)
        self._value.setText(f"{level}%")
        color = GREEN if level > 50 else CYAN if level > 20 else YELLOW
        self._value.setStyleSheet(f"color:{color};font-size:12px;min-width:40px;")

    def reset(self):
        self._bar.setValue(0)
        self._value.setText("0%")
        self._value.setStyleSheet(f"color:{TEXT_DIM};font-size:12px;min-width:40px;")


if __name__ == "__main__":
    app = QApplication([])
    w = AudioBarComponent()
    w.setStyleSheet(f"background:{BG};")
    w.set_level(65)
    w.show()
    app.exec_()
