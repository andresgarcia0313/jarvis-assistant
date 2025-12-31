"""
Sistema de diagnóstico de inicio para JARVIS.
Valida todos los componentes antes de iniciar la interfaz.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Callable
from datetime import datetime

from ui.logger_config import get_logger

logger = get_logger(__name__)


@dataclass
class DiagnosticResult:
    """Resultado de un diagnóstico individual."""
    name: str
    status: str  # "ok", "warning", "error"
    message: str
    details: Optional[str] = None


class SystemDiagnostics:
    """Ejecuta diagnósticos de todos los componentes de JARVIS."""

    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.results: List[DiagnosticResult] = []
        self._progress_callback: Optional[Callable] = None

    def set_progress_callback(self, callback: Callable):
        """Configura callback para reportar progreso."""
        self._progress_callback = callback

    def _report(self, result: DiagnosticResult):
        """Reporta resultado de diagnóstico."""
        self.results.append(result)
        logger.info(f"[DIAG] {result.name}: {result.status} - {result.message}")
        if self._progress_callback:
            self._progress_callback(result)

    def run_all(self) -> bool:
        """Ejecuta todos los diagnósticos. Retorna True si todo está OK."""
        self.results.clear()
        logger.info("=== Iniciando diagnóstico del sistema ===")

        # 1. Modelo de voz (STT)
        self._check_vosk_model()

        # 2. Motor TTS
        self._check_tts()

        # 3. Claude CLI (IA)
        self._check_claude_cli()

        # 4. Audio (PyAudio)
        self._check_audio()

        # 5. Dependencias Python
        self._check_python_deps()

        # 6. Permisos de directorios
        self._check_directories()

        # Resultado final
        errors = [r for r in self.results if r.status == "error"]
        warnings = [r for r in self.results if r.status == "warning"]

        if errors:
            logger.error(f"Diagnóstico: {len(errors)} errores, {len(warnings)} advertencias")
            return False

        logger.info(f"Diagnóstico completado: {len(warnings)} advertencias, sistema operativo")
        return True

    def _check_vosk_model(self):
        """Verifica que el modelo Vosk esté disponible."""
        if self.model_path.exists():
            # Verificar archivos clave del modelo
            required_files = ["conf/model.conf", "am/final.mdl"]
            missing = [f for f in required_files if not (self.model_path / f).exists()]

            if missing:
                self._report(DiagnosticResult(
                    name="Modelo STT",
                    status="warning",
                    message="Modelo incompleto",
                    details=f"Archivos faltantes: {missing}"
                ))
            else:
                size_mb = sum(f.stat().st_size for f in self.model_path.rglob("*") if f.is_file()) / 1024 / 1024
                self._report(DiagnosticResult(
                    name="Modelo STT",
                    status="ok",
                    message=f"Vosk cargado ({size_mb:.1f}MB)"
                ))
        else:
            self._report(DiagnosticResult(
                name="Modelo STT",
                status="error",
                message="Modelo Vosk no encontrado",
                details=str(self.model_path)
            ))

    def _check_tts(self):
        """Verifica que el motor TTS esté disponible."""
        # Verificar espeak-ng
        espeak_path = shutil.which("espeak-ng")
        if espeak_path:
            try:
                result = subprocess.run(
                    ["espeak-ng", "--version"],
                    capture_output=True, text=True, timeout=5
                )
                version = result.stdout.strip().split('\n')[0] if result.stdout else "unknown"
                self._report(DiagnosticResult(
                    name="Motor TTS",
                    status="ok",
                    message=f"espeak-ng disponible",
                    details=version
                ))
                return
            except Exception as e:
                pass

        # Verificar piper como alternativa
        piper_path = shutil.which("piper")
        if piper_path:
            self._report(DiagnosticResult(
                name="Motor TTS",
                status="ok",
                message="piper disponible"
            ))
            return

        self._report(DiagnosticResult(
            name="Motor TTS",
            status="error",
            message="No hay motor TTS disponible",
            details="Instalar: sudo apt install espeak-ng"
        ))

    def _check_claude_cli(self):
        """Verifica que Claude CLI esté disponible."""
        # Buscar en PATH
        claude_path = shutil.which("claude")

        # Buscar en ubicaciones conocidas
        if not claude_path:
            known_paths = [
                Path.home() / ".local" / "bin" / "claude",
                Path.home() / ".npm-global" / "bin" / "claude",
                Path("/usr/local/bin/claude"),
                Path("/usr/bin/claude"),
            ]
            for path in known_paths:
                if path.exists() and os.access(path, os.X_OK):
                    claude_path = str(path)
                    break

        if claude_path:
            try:
                result = subprocess.run(
                    [claude_path, "--version"],
                    capture_output=True, text=True, timeout=10
                )
                version = result.stdout.strip() if result.stdout else "disponible"
                self._report(DiagnosticResult(
                    name="Claude CLI",
                    status="ok",
                    message="IA disponible",
                    details=f"{claude_path}"
                ))
            except Exception as e:
                self._report(DiagnosticResult(
                    name="Claude CLI",
                    status="warning",
                    message="Claude encontrado pero no responde",
                    details=str(e)
                ))
        else:
            self._report(DiagnosticResult(
                name="Claude CLI",
                status="error",
                message="Claude CLI no encontrado",
                details="Instalar: npm install -g @anthropic-ai/claude-code"
            ))

    def _check_audio(self):
        """Verifica que el sistema de audio esté funcionando."""
        try:
            import pyaudio
            pa = pyaudio.PyAudio()

            # Contar dispositivos de entrada
            input_devices = []
            for i in range(pa.get_device_count()):
                info = pa.get_device_info_by_index(i)
                if info.get('maxInputChannels', 0) > 0:
                    input_devices.append(info['name'])

            pa.terminate()

            if input_devices:
                self._report(DiagnosticResult(
                    name="Sistema Audio",
                    status="ok",
                    message=f"{len(input_devices)} micrófono(s) detectado(s)",
                    details=input_devices[0] if input_devices else None
                ))
            else:
                self._report(DiagnosticResult(
                    name="Sistema Audio",
                    status="warning",
                    message="No hay micrófonos detectados"
                ))

        except ImportError:
            self._report(DiagnosticResult(
                name="Sistema Audio",
                status="error",
                message="PyAudio no instalado",
                details="pip install pyaudio"
            ))
        except Exception as e:
            self._report(DiagnosticResult(
                name="Sistema Audio",
                status="error",
                message=f"Error de audio: {e}"
            ))

    def _check_python_deps(self):
        """Verifica dependencias Python críticas."""
        required = {
            "vosk": "Reconocimiento de voz",
            "PyQt5": "Interfaz gráfica",
            "numpy": "Procesamiento de audio",
        }

        missing = []
        for module, desc in required.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(f"{module} ({desc})")

        if missing:
            self._report(DiagnosticResult(
                name="Dependencias Python",
                status="error",
                message=f"{len(missing)} módulo(s) faltante(s)",
                details=", ".join(missing)
            ))
        else:
            self._report(DiagnosticResult(
                name="Dependencias Python",
                status="ok",
                message="Todas las dependencias instaladas"
            ))

    def _check_directories(self):
        """Verifica permisos en directorios necesarios."""
        dirs_to_check = [
            Path.home() / ".local" / "share" / "jarvis",
            Path.home() / ".local" / "share" / "jarvis" / "logs",
        ]

        issues = []
        for dir_path in dirs_to_check:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                # Verificar escritura
                test_file = dir_path / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
            except Exception as e:
                issues.append(f"{dir_path}: {e}")

        if issues:
            self._report(DiagnosticResult(
                name="Permisos",
                status="warning",
                message="Problemas de permisos",
                details="; ".join(issues)
            ))
        else:
            self._report(DiagnosticResult(
                name="Permisos",
                status="ok",
                message="Directorios accesibles"
            ))

    def get_summary(self) -> dict:
        """Retorna resumen de diagnósticos."""
        return {
            "total": len(self.results),
            "ok": len([r for r in self.results if r.status == "ok"]),
            "warnings": len([r for r in self.results if r.status == "warning"]),
            "errors": len([r for r in self.results if r.status == "error"]),
            "results": self.results,
            "timestamp": datetime.now().isoformat()
        }
