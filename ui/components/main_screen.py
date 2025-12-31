"""
MainScreen - Pantalla principal de JARVIS.

Componente autocontenido que compone los demás componentes.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QApplication
from .theme import BG, BORDER
from .header import HeaderComponent
from .audio_bar import AudioBarComponent
from .text_panels import VoiceInputPanel, AIResponsePanel, SystemLogPanel
from .controls import ControlsComponent


class MainScreen(QWidget):
    """Pantalla principal con todos los componentes de JARVIS."""

    def __init__(self, on_config=None, on_toggle=None, on_clear=None):
        super().__init__()
        self.setStyleSheet(f"background:{BG};")
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # Header
        self.header = HeaderComponent(on_config=on_config)
        layout.addWidget(self.header)

        # Audio bar
        self.audio_bar = AudioBarComponent()
        layout.addWidget(self.audio_bar)

        # Separator
        layout.addWidget(self._sep())

        # Voice input panel
        self.voice_input = VoiceInputPanel()
        layout.addWidget(self.voice_input)

        # AI response panel
        self.ai_response = AIResponsePanel()
        layout.addWidget(self.ai_response, 1)

        # System log panel
        self.system_log = SystemLogPanel()
        layout.addWidget(self.system_log)

        # Separator
        layout.addWidget(self._sep())

        # Controls
        self.controls = ControlsComponent(on_toggle=on_toggle, on_clear=on_clear)
        layout.addWidget(self.controls)

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background:{BORDER};")
        sep.setFixedHeight(1)
        return sep

    # Convenience methods
    def set_status(self, text: str, active: bool = False):
        self.header.set_status(text, active)

    def set_status_custom(self, text: str, style: str):
        self.header.set_status_custom(text, style)

    def set_audio_level(self, level: int):
        self.audio_bar.set_level(level)

    def reset_audio(self):
        self.audio_bar.reset()

    def append_voice_input(self, text: str):
        self.voice_input.append(text)

    def append_response(self, text: str):
        self.ai_response.append(text)

    def append_log(self, text: str):
        self.system_log.append(text)

    def clear_all(self):
        self.voice_input.clear()
        self.ai_response.clear()
        self.system_log.clear()

    def set_active(self, active: bool):
        self.controls.set_active(active)

    def is_active(self) -> bool:
        return self.controls.is_active()


if __name__ == "__main__":
    app = QApplication([])
    w = MainScreen(
        on_config=lambda: print("Config"),
        on_toggle=lambda: print("Toggle"),
        on_clear=lambda: print("Clear")
    )
    w.append_voice_input("Hello JARVIS")
    w.append_response("Hello, how can I help you?")
    w.append_log("[12:00:00] [+] System ready")
    w.set_audio_level(45)
    w.resize(850, 700)
    w.show()
    app.exec_()
