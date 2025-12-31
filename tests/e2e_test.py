#!/usr/bin/env python3
"""
Prueba E2E para JARVIS con capturas de pantalla.
"""

import subprocess
import time
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
SCREENSHOTS_DIR = PROJECT_ROOT / "tests" / "screenshots"
LOG_FILE = PROJECT_ROOT / "tests" / "e2e_test.log"


def log(msg: str):
    """Log con timestamp."""
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")


def screenshot(name: str) -> str:
    """Toma captura de pantalla completa."""
    SCREENSHOTS_DIR.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%H%M%S")
    filepath = SCREENSHOTS_DIR / f"{ts}_{name}.png"

    try:
        # Captura de pantalla completa con spectacle
        subprocess.run(
            ["spectacle", "-f", "-b", "-n", "-o", str(filepath)],
            capture_output=True, timeout=10
        )
        if filepath.exists():
            log(f"📸 Captura: {filepath.name}")
            return str(filepath)

        log(f"⚠ No se pudo capturar pantalla")
        return ""

    except Exception as e:
        log(f"⚠ Error en captura: {e}")
        return ""


def speak_command(text: str):
    """Reproduce audio con el comando usando espeak-ng."""
    log(f"🔊 Reproduciendo: '{text}'")
    try:
        # Generar audio
        subprocess.run(
            ["espeak-ng", "-v", "es", "-s", "150", text],
            timeout=10
        )
        time.sleep(0.5)
    except Exception as e:
        log(f"⚠ Error reproduciendo audio: {e}")


def start_jarvis() -> subprocess.Popen:
    """Inicia JARVIS GUI."""
    log("🚀 Iniciando JARVIS...")
    proc = subprocess.Popen(
        ["jarvis-gui"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    time.sleep(3)  # Esperar a que cargue
    return proc


def test_startup():
    """Prueba: Inicio de JARVIS."""
    log("=" * 50)
    log("TEST 1: Inicio de JARVIS")
    log("=" * 50)

    proc = start_jarvis()
    screenshot("01_inicio")

    # Verificar que está corriendo
    if proc.poll() is None:
        log("✓ JARVIS iniciado correctamente")
        return proc
    else:
        log("✗ JARVIS falló al iniciar")
        return None


def test_activate_mic(proc):
    """Prueba: Activar micrófono simulando click."""
    log("=" * 50)
    log("TEST 2: Activar micrófono")
    log("=" * 50)

    try:
        # Buscar ventana y hacer click en botón activar
        result = subprocess.run(
            ["xdotool", "search", "--name", "JARVIS"],
            capture_output=True, text=True, timeout=5
        )
        window_id = result.stdout.strip().split('\n')[0]

        if window_id:
            # Activar ventana
            subprocess.run(["xdotool", "windowactivate", window_id], timeout=5)
            time.sleep(0.5)

            # Click en botón (parte inferior de la ventana)
            subprocess.run([
                "xdotool", "mousemove", "--window", window_id,
                "300", "850"  # Posición aproximada del botón
            ], timeout=5)
            subprocess.run(["xdotool", "click", "1"], timeout=5)

            time.sleep(1)
            screenshot("02_microfono_activado")
            log("✓ Click en botón de micrófono")
        else:
            log("⚠ No se encontró ventana JARVIS")
    except Exception as e:
        log(f"⚠ Error activando micrófono: {e}")


def test_voice_command(proc):
    """Prueba: Enviar comando de voz."""
    log("=" * 50)
    log("TEST 3: Comando de voz 'Jarvis hola'")
    log("=" * 50)

    screenshot("03_antes_comando")

    # Reproducir comando
    speak_command("Jarvis, hola, cómo estás")

    time.sleep(2)
    screenshot("04_despues_comando")

    # Esperar respuesta
    log("⏳ Esperando respuesta de IA...")
    time.sleep(10)
    screenshot("05_respuesta")


def test_shutdown(proc):
    """Prueba: Cerrar JARVIS."""
    log("=" * 50)
    log("TEST 4: Cerrar JARVIS")
    log("=" * 50)

    if proc:
        proc.terminate()
        proc.wait(timeout=5)
        log("✓ JARVIS cerrado correctamente")


def run_all_tests():
    """Ejecuta todas las pruebas."""
    # Limpiar log anterior
    LOG_FILE.parent.mkdir(exist_ok=True)
    if LOG_FILE.exists():
        LOG_FILE.unlink()

    log("=" * 50)
    log("INICIANDO PRUEBAS E2E DE JARVIS")
    log("=" * 50)

    proc = None
    try:
        proc = test_startup()
        if proc:
            test_activate_mic(proc)
            test_voice_command(proc)
    except Exception as e:
        log(f"✗ Error en pruebas: {e}")
        screenshot("error")
    finally:
        if proc:
            test_shutdown(proc)

    log("=" * 50)
    log("PRUEBAS COMPLETADAS")
    log(f"Capturas en: {SCREENSHOTS_DIR}")
    log(f"Log en: {LOG_FILE}")
    log("=" * 50)


if __name__ == "__main__":
    run_all_tests()
