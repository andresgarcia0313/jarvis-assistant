"""
Componentes UI de JARVIS - Arquitectura estilo Vue.

Cada componente es autocontenido con estilos inline y testeable de forma independiente.
"""
from .theme import CYAN, GREEN, YELLOW, RED, BG, BORDER, TEXT, TEXT_DIM
from .header import HeaderComponent
from .audio_bar import AudioBarComponent
from .text_panels import TextPanel, VoiceInputPanel, AIResponsePanel, SystemLogPanel
from .controls import ControlsComponent
from .diagnostics_screen import DiagnosticsScreen
from .main_screen import MainScreen

__all__ = [
    # Theme
    'CYAN', 'GREEN', 'YELLOW', 'RED', 'BG', 'BORDER', 'TEXT', 'TEXT_DIM',
    # Components
    'HeaderComponent',
    'AudioBarComponent',
    'TextPanel',
    'VoiceInputPanel',
    'AIResponsePanel',
    'SystemLogPanel',
    'ControlsComponent',
    'DiagnosticsScreen',
    'MainScreen',
]
