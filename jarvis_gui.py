#!/usr/bin/env python3
"""
JARVIS HUD - Interfaz futurista con IA integrada.
"""

import os
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PyQt5.QtWidgets import QApplication
from ui.hud_gui import JarvisHUD

MODEL_PATH = "models/vosk-model-small-es-0.42"


def main():
    parser = argparse.ArgumentParser(description="JARVIS Voice Assistant")
    parser.add_argument("--test", action="store_true", help="Modo test (capturas automáticas)")
    parser.add_argument("--pid-file", type=str, help="Archivo donde guardar el PID")
    args = parser.parse_args()

    # Guardar PID si se solicita (para E2E tests)
    if args.pid_file:
        Path(args.pid_file).write_text(str(os.getpid()))

    model_full_path = PROJECT_ROOT / MODEL_PATH

    if not model_full_path.exists():
        print(f"Error: Modelo no encontrado en {model_full_path}")
        print("Ejecuta: ./install.sh para descargar modelos")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = JarvisHUD(str(model_full_path), test_mode=args.test)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
