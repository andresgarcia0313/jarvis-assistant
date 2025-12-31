"""
TextPanels - Paneles de texto (Voice Input, AI Response, System Log).

Componentes autocontenidos con estilos inline.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt
from .theme import CYAN, BG, BORDER, TEXT, TEXT_DIM, GREEN


class TextPanel(QWidget):
    """Panel de texto genérico."""

    def __init__(self, title: str, color: str, placeholder: str = "",
                 max_h: int = None, expand: bool = False):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        label = QLabel(title)
        label.setStyleSheet(f"color:{color};font-size:11px;font-weight:600;letter-spacing:2px;")
        layout.addWidget(label)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setPlaceholderText(placeholder)
        self._text.setStyleSheet(f"""
            QTextEdit {{
                background:{BG};color:{TEXT};border:1px solid {color}40;
                border-left:3px solid {color};border-radius:4px;padding:8px;
            }}
        """)
        if max_h:
            self._text.setMaximumHeight(max_h)
        if expand:
            self._text.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self._text, 1 if expand else 0)

    def append(self, text: str):
        self._text.append(text)
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self):
        self._text.clear()


class VoiceInputPanel(TextPanel):
    """Panel de entrada de voz (verde)."""
    def __init__(self):
        super().__init__("VOICE INPUT", GREEN, "Say 'JARVIS' followed by your command...", max_h=140)


class AIResponsePanel(TextPanel):
    """Panel de respuestas IA (cyan)."""
    def __init__(self):
        super().__init__("AI RESPONSE", CYAN, "JARVIS responses will appear here...", expand=True)


class SystemLogPanel(QWidget):
    """Panel de log colapsable."""

    STYLE_LABEL = f"color:{TEXT_DIM};font-size:11px;font-weight:600;letter-spacing:2px;"
    STYLE_BTN = f"background:{BG};color:{TEXT_DIM};border:1px solid {BORDER};font-size:10px;"
    STYLE_TEXT = f"""
        QTextEdit {{
            background:{BG};color:{TEXT_DIM};border:1px solid {BORDER};
            border-radius:4px;padding:6px;font-size:11px;
        }}
    """

    def __init__(self):
        super().__init__()
        self._collapsed = False
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        header = QHBoxLayout()
        label = QLabel("SYSTEM LOG")
        label.setStyleSheet(self.STYLE_LABEL)
        header.addWidget(label)
        header.addStretch()

        self._btn = QPushButton("HIDE")
        self._btn.setFixedSize(50, 22)
        self._btn.setStyleSheet(self.STYLE_BTN)
        self._btn.setCursor(Qt.PointingHandCursor)
        self._btn.clicked.connect(self._toggle)
        header.addWidget(self._btn)
        layout.addLayout(header)

        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setMaximumHeight(90)
        self._text.setStyleSheet(self.STYLE_TEXT)
        layout.addWidget(self._text)

    def _toggle(self):
        self._collapsed = not self._collapsed
        self._text.setVisible(not self._collapsed)
        self._btn.setText("SHOW" if self._collapsed else "HIDE")

    def append(self, text: str):
        self._text.append(text)
        sb = self._text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def clear(self):
        self._text.clear()


if __name__ == "__main__":
    app = QApplication([])
    from PyQt5.QtWidgets import QVBoxLayout as VBox

    container = QWidget()
    container.setStyleSheet(f"background:{BG};")
    layout = VBox(container)

    v = VoiceInputPanel()
    v.append("Test voice input")
    layout.addWidget(v)

    a = AIResponsePanel()
    a.append("Test AI response")
    layout.addWidget(a)

    s = SystemLogPanel()
    s.append("[12:00:00] [+] System ready")
    layout.addWidget(s)

    container.resize(600, 500)
    container.show()
    app.exec_()
