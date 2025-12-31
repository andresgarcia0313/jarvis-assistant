"""
Diálogo de configuración de JARVIS.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QPushButton, QLineEdit, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt
from ui.audio_devices import AudioDeviceManager

COLORS = {
    "bg_dark": "#050a0f",
    "bg_panel": "#0a1520",
    "cyan": "#00d4ff",
    "green": "#00ff88",
    "text": "#e0e0e0",
}


class ConfigDialog(QDialog):
    """Diálogo para configurar JARVIS."""

    def __init__(self, parent=None, current_mode="repl", api_key="",
                 current_device=None, tts_enabled=True):
        super().__init__(parent)
        self.setWindowTitle("Configuración JARVIS")
        self.setMinimumWidth(550)
        self.mode = current_mode
        self.api_key = api_key
        self.current_device = current_device
        self.tts_enabled = tts_enabled
        self.audio_manager = AudioDeviceManager()
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['bg_dark']};
                color: {COLORS['text']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: 14px;
            }}
            QGroupBox {{
                color: {COLORS['cyan']};
                font-size: 16px;
                font-weight: bold;
                border: 2px solid {COLORS['cyan']};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
            QComboBox, QLineEdit {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['text']};
                border: 1px solid {COLORS['cyan']};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}
            QPushButton {{
                background-color: {COLORS['bg_panel']};
                color: {COLORS['cyan']};
                border: 2px solid {COLORS['cyan']};
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: #1a2530;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Grupo: Modo de comunicación
        mode_group = QGroupBox("Modo de Comunicación con IA")
        mode_layout = QVBoxLayout(mode_group)

        mode_info = QLabel(
            "REPL: Usa Claude Code instalado en tu terminal (gratis, local)\n"
            "API: Conexión directa a Anthropic (requiere API key, más rápido)"
        )
        mode_info.setStyleSheet("color: #888; font-size: 12px;")
        mode_layout.addWidget(mode_info)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Modo:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["REPL (Claude Code)", "API (Anthropic)"])
        self.mode_combo.setCurrentIndex(0 if self.mode == "repl" else 1)
        self.mode_combo.currentIndexChanged.connect(self._on_mode_change)
        mode_row.addWidget(self.mode_combo, 1)
        mode_layout.addLayout(mode_row)

        layout.addWidget(mode_group)

        # Grupo: API Key (solo si es API)
        self.api_group = QGroupBox("Configuración API")
        api_layout = QVBoxLayout(self.api_group)

        api_row = QHBoxLayout()
        api_row.addWidget(QLabel("API Key:"))
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("sk-ant-...")
        self.api_input.setText(self.api_key)
        self.api_input.setEchoMode(QLineEdit.Password)
        api_row.addWidget(self.api_input, 1)
        api_layout.addLayout(api_row)

        self.api_group.setVisible(self.mode == "api")
        layout.addWidget(self.api_group)

        # Grupo: Audio
        audio_group = QGroupBox("Audio")
        audio_layout = QVBoxLayout(audio_group)

        # Selector de micrófono
        mic_row = QHBoxLayout()
        mic_row.addWidget(QLabel("Micrófono:"))
        self.mic_combo = QComboBox()
        self._populate_microphones()
        mic_row.addWidget(self.mic_combo, 1)

        refresh_btn = QPushButton("↻")
        refresh_btn.setMaximumWidth(40)
        refresh_btn.clicked.connect(self._refresh_devices)
        mic_row.addWidget(refresh_btn)
        audio_layout.addLayout(mic_row)

        # TTS habilitado
        self.tts_checkbox = QCheckBox("Habilitar voz (TTS)")
        self.tts_checkbox.setChecked(self.tts_enabled)
        self.tts_checkbox.setStyleSheet(f"color: {COLORS['text']}; font-size: 14px;")
        audio_layout.addWidget(self.tts_checkbox)

        layout.addWidget(audio_group)

        # Botones
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Guardar")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _populate_microphones(self):
        """Llena el combo de micrófonos."""
        self.mic_combo.clear()
        devices = self.audio_manager.get_input_devices()
        current_idx = 0

        for i, dev in enumerate(devices):
            label = f"{dev['name']} ({dev['channels']}ch)"
            if dev['is_default']:
                label += " [Default]"
            self.mic_combo.addItem(label, dev['index'])
            if dev['index'] == self.current_device:
                current_idx = i
            elif self.current_device is None and dev['is_default']:
                current_idx = i

        if devices:
            self.mic_combo.setCurrentIndex(current_idx)

    def _refresh_devices(self):
        """Refresca la lista de dispositivos."""
        self.audio_manager.refresh()
        self._populate_microphones()

    def _on_mode_change(self, index):
        self.api_group.setVisible(index == 1)

    def get_config(self):
        device_idx = None
        if self.mic_combo.count() > 0:
            device_idx = self.mic_combo.currentData()

        return {
            "mode": "repl" if self.mode_combo.currentIndex() == 0 else "api",
            "api_key": self.api_input.text(),
            "device": device_idx,
            "tts_enabled": self.tts_checkbox.isChecked()
        }
