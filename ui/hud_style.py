"""
HUD Style - Compatibilidad hacia atrás.

Los componentes usan estilos inline. Este archivo existe para código legacy.
"""
from ui.components.theme import CYAN, GREEN, YELLOW, RED, BG, BORDER, TEXT, TEXT_DIM

# Legacy COLORS dict
COLORS = {
    "arc": CYAN, "arc_bright": "#80efff", "arc_dim": "#00a8cc",
    "success": GREEN, "warning": YELLOW, "error": RED, "accent": CYAN,
    "bg_dark": BG, "bg_panel": "#0a1a24", "bg_input": "#061018",
    "border": BORDER, "text": TEXT, "text_secondary": TEXT_DIM, "text_muted": TEXT_DIM,
}

MAIN_STYLE = f"background:{BG};color:{TEXT};font-family:sans-serif;"


def get_status_style(active: bool) -> str:
    c = GREEN if active else TEXT_DIM
    return f"color:{c};background:{c}20;padding:4px 12px;border-radius:12px;border:1px solid {c};"


def get_audio_level_color(level: int) -> str:
    return GREEN if level > 50 else CYAN if level > 20 else YELLOW


def get_diag_style(status: str) -> str:
    c = {"ok": GREEN, "warning": YELLOW, "error": RED}.get(status, TEXT_DIM)
    return f"color:{c};"
