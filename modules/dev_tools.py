"""
JARVIS Developer Tools Module
Provides developer-focused commands: git, docker, tests, file reading, logs.
"""

import subprocess
import shutil
import logging
import re
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Result of a command execution."""
    success: bool
    output: str
    error: Optional[str] = None


class GitTools:
    """Git-related commands and queries."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()

    def _run_git(self, *args, timeout: int = 30) -> CommandResult:
        """Run a git command."""
        if not shutil.which("git"):
            return CommandResult(False, "", "Git no está instalado")

        try:
            result = subprocess.run(
                ["git"] + list(args),
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip() if result.returncode != 0 else None
            )
        except subprocess.TimeoutExpired:
            return CommandResult(False, "", "El comando tardó demasiado")
        except Exception as e:
            return CommandResult(False, "", str(e))

    def is_git_repo(self) -> bool:
        """Check if current directory is a git repository."""
        result = self._run_git("rev-parse", "--git-dir")
        return result.success

    def get_status(self) -> str:
        """Get git status summary."""
        if not self.is_git_repo():
            return "Este directorio no es un repositorio git."

        result = self._run_git("status", "--porcelain")
        if not result.success:
            return f"Error al obtener estado: {result.error}"

        if not result.output:
            return "El repositorio está limpio. No hay cambios pendientes."

        lines = result.output.split('\n')
        modified = sum(1 for l in lines if l.startswith(' M') or l.startswith('M '))
        added = sum(1 for l in lines if l.startswith('A ') or l.startswith('??'))
        deleted = sum(1 for l in lines if l.startswith(' D') or l.startswith('D '))

        parts = []
        if modified:
            parts.append(f"{modified} archivo{'s' if modified > 1 else ''} modificado{'s' if modified > 1 else ''}")
        if added:
            parts.append(f"{added} archivo{'s' if added > 1 else ''} nuevo{'s' if added > 1 else ''}")
        if deleted:
            parts.append(f"{deleted} archivo{'s' if deleted > 1 else ''} eliminado{'s' if deleted > 1 else ''}")

        return "Cambios pendientes: " + ", ".join(parts) + "."

    def get_uncommitted_changes(self) -> str:
        """Get list of uncommitted changes."""
        if not self.is_git_repo():
            return "Este directorio no es un repositorio git."

        result = self._run_git("status", "--short")
        if not result.success:
            return f"Error: {result.error}"

        if not result.output:
            return "No hay cambios sin commitear."

        lines = result.output.split('\n')[:10]
        summary = "Archivos modificados:\n"
        for line in lines:
            if line.strip():
                summary += f"  {line}\n"

        if len(result.output.split('\n')) > 10:
            summary += f"  ... y {len(result.output.split(chr(10))) - 10} más."

        return summary

    def get_current_branch(self) -> str:
        """Get current branch name."""
        if not self.is_git_repo():
            return "No es un repositorio git."

        result = self._run_git("branch", "--show-current")
        if result.success and result.output:
            return f"Está en la rama {result.output}."
        return "No se pudo determinar la rama actual."

    def get_recent_commits(self, count: int = 5) -> str:
        """Get recent commits."""
        if not self.is_git_repo():
            return "No es un repositorio git."

        result = self._run_git(
            "log", f"-{count}",
            "--oneline", "--no-decorate"
        )
        if not result.success:
            return f"Error: {result.error}"

        if not result.output:
            return "No hay commits en este repositorio."

        lines = result.output.split('\n')
        summary = f"Últimos {len(lines)} commits:\n"
        for line in lines:
            summary += f"  - {line}\n"

        return summary

    def get_diff_summary(self) -> str:
        """Get a summary of current diff."""
        if not self.is_git_repo():
            return "No es un repositorio git."

        result = self._run_git("diff", "--stat")
        if not result.success:
            return f"Error: {result.error}"

        if not result.output:
            return "No hay diferencias en archivos tracked."

        lines = result.output.split('\n')
        # Last line usually has the summary
        if lines:
            return f"Diferencias: {lines[-1]}"
        return "No hay diferencias."


class DockerTools:
    """Docker-related commands and queries."""

    def __init__(self):
        self.has_docker = shutil.which("docker") is not None

    def _run_docker(self, *args, timeout: int = 30) -> CommandResult:
        """Run a docker command."""
        if not self.has_docker:
            return CommandResult(False, "", "Docker no está instalado")

        try:
            result = subprocess.run(
                ["docker"] + list(args),
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return CommandResult(
                success=result.returncode == 0,
                output=result.stdout.strip(),
                error=result.stderr.strip() if result.returncode != 0 else None
            )
        except subprocess.TimeoutExpired:
            return CommandResult(False, "", "El comando tardó demasiado")
        except Exception as e:
            return CommandResult(False, "", str(e))

    def get_containers_status(self) -> str:
        """Get status of all containers."""
        if not self.has_docker:
            return "Docker no está instalado en este sistema."

        result = self._run_docker("ps", "-a", "--format",
                                  "{{.Names}}\t{{.Status}}\t{{.Image}}")
        if not result.success:
            return f"Error al consultar Docker: {result.error}"

        if not result.output:
            return "No hay contenedores Docker."

        lines = result.output.split('\n')
        running = sum(1 for l in lines if 'Up' in l)
        stopped = len(lines) - running

        summary = f"Contenedores: {running} activo{'s' if running != 1 else ''}, "
        summary += f"{stopped} detenido{'s' if stopped != 1 else ''}.\n"

        for line in lines[:5]:
            parts = line.split('\t')
            if len(parts) >= 2:
                name = parts[0]
                status = "activo" if "Up" in parts[1] else "detenido"
                summary += f"  - {name}: {status}\n"

        if len(lines) > 5:
            summary += f"  ... y {len(lines) - 5} más."

        return summary

    def get_running_containers(self) -> str:
        """Get list of running containers."""
        if not self.has_docker:
            return "Docker no está instalado."

        result = self._run_docker("ps", "--format", "{{.Names}}: {{.Image}}")
        if not result.success:
            return f"Error: {result.error}"

        if not result.output:
            return "No hay contenedores en ejecución."

        lines = result.output.split('\n')
        return f"Contenedores activos ({len(lines)}):\n" + "\n".join(f"  - {l}" for l in lines)

    def get_container_logs(self, container: str, lines: int = 20) -> str:
        """Get logs from a container."""
        if not self.has_docker:
            return "Docker no está instalado."

        result = self._run_docker("logs", "--tail", str(lines), container)
        if not result.success:
            return f"Error al obtener logs: {result.error}"

        return f"Últimas {lines} líneas de {container}:\n{result.output}"


class TestRunner:
    """Test execution tools."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()

    def detect_test_framework(self) -> Optional[str]:
        """Detect which test framework is used."""
        path = Path(self.working_dir)

        # Python
        if (path / "pytest.ini").exists() or (path / "pyproject.toml").exists():
            if shutil.which("pytest"):
                return "pytest"
        if (path / "setup.py").exists():
            return "python -m unittest"

        # JavaScript/TypeScript
        if (path / "package.json").exists():
            try:
                import json
                with open(path / "package.json") as f:
                    pkg = json.load(f)
                    scripts = pkg.get("scripts", {})
                    if "test" in scripts:
                        return "npm test"
            except Exception:
                pass

        # Go
        if any(path.glob("*_test.go")):
            return "go test"

        # Rust
        if (path / "Cargo.toml").exists():
            return "cargo test"

        return None

    def run_tests(self, framework: Optional[str] = None) -> str:
        """Run tests using detected or specified framework."""
        if not framework:
            framework = self.detect_test_framework()

        if not framework:
            return "No pude detectar el framework de tests. Especifica cómo ejecutarlos."

        try:
            result = subprocess.run(
                framework.split(),
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes max
            )

            if result.returncode == 0:
                # Extract summary from output
                output = result.stdout
                if "passed" in output.lower():
                    match = re.search(r'(\d+)\s*passed', output)
                    if match:
                        return f"Tests completados: {match.group(1)} pasaron."
                return "Tests ejecutados correctamente."
            else:
                # Try to extract failure info
                output = result.stdout + result.stderr
                failed_match = re.search(r'(\d+)\s*failed', output)
                if failed_match:
                    return f"Tests fallaron: {failed_match.group(1)} errores."
                return f"Tests fallaron. Revisa el log para más detalles."

        except subprocess.TimeoutExpired:
            return "Los tests tardaron demasiado y fueron cancelados."
        except Exception as e:
            return f"Error al ejecutar tests: {e}"


class FileReader:
    """File reading and log analysis tools."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()

    def read_file(self, filename: str, lines: int = 50) -> str:
        """Read a file and return its content."""
        path = Path(self.working_dir) / filename

        if not path.exists():
            # Try absolute path
            path = Path(filename)
            if not path.exists():
                return f"No encontré el archivo {filename}."

        if not path.is_file():
            return f"{filename} no es un archivo."

        # Check file size
        if path.stat().st_size > 1024 * 1024:  # 1MB limit
            return f"El archivo {filename} es demasiado grande para leer completo."

        try:
            with open(path, 'r', errors='ignore') as f:
                content = f.readlines()

            if len(content) > lines:
                content = content[:lines]
                truncated = True
            else:
                truncated = False

            result = f"Contenido de {filename}:\n"
            result += "".join(content)

            if truncated:
                result += f"\n... (mostrando primeras {lines} líneas)"

            return result

        except Exception as e:
            return f"Error al leer {filename}: {e}"

    def read_log_errors(self, log_file: str, lines: int = 30) -> str:
        """Read errors from a log file."""
        path = Path(self.working_dir) / log_file

        if not path.exists():
            path = Path(log_file)
            if not path.exists():
                return f"No encontré el archivo de log {log_file}."

        try:
            with open(path, 'r', errors='ignore') as f:
                content = f.read()

            # Find error lines
            error_patterns = [
                r'(?i)error[:\s].*',
                r'(?i)exception[:\s].*',
                r'(?i)failed[:\s].*',
                r'(?i)fatal[:\s].*',
            ]

            errors = []
            for line in content.split('\n'):
                for pattern in error_patterns:
                    if re.search(pattern, line):
                        errors.append(line.strip())
                        break

            if not errors:
                return f"No encontré errores en {log_file}."

            result = f"Errores encontrados en {log_file} ({len(errors)} total):\n"
            for error in errors[-lines:]:
                result += f"  {error[:100]}\n"

            return result

        except Exception as e:
            return f"Error al leer {log_file}: {e}"

    def find_files(self, pattern: str, max_results: int = 10) -> str:
        """Find files matching a pattern."""
        path = Path(self.working_dir)

        try:
            matches = list(path.rglob(pattern))[:max_results]

            if not matches:
                return f"No encontré archivos que coincidan con {pattern}."

            result = f"Archivos encontrados ({len(matches)}):\n"
            for match in matches:
                rel_path = match.relative_to(path)
                result += f"  - {rel_path}\n"

            return result

        except Exception as e:
            return f"Error al buscar: {e}"


class DevToolsManager:
    """Main manager for developer tools."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.git = GitTools(self.working_dir)
        self.docker = DockerTools()
        self.tests = TestRunner(self.working_dir)
        self.files = FileReader(self.working_dir)

    def set_working_dir(self, path: str) -> str:
        """Change working directory."""
        if os.path.isdir(path):
            self.working_dir = path
            self.git.working_dir = path
            self.tests.working_dir = path
            self.files.working_dir = path
            return f"Directorio de trabajo cambiado a {path}."
        return f"El directorio {path} no existe."


class DevQueryHandler:
    """Handles developer-related queries."""

    GIT_PATTERNS = [
        (r"(?:qu[eé]\s+)?cambios\s+(?:tengo\s+)?sin\s+commit(?:ear)?", "uncommitted"),
        (r"estado\s+(?:del\s+)?(?:repo|repositorio|git)", "status"),
        (r"(?:qu[eé]\s+)?rama\s+(?:estoy|actual)", "branch"),
        (r"[uú]ltimos?\s+commits?", "commits"),
        (r"(?:qu[eé]\s+)?diferencias", "diff"),
        (r"git\s+status", "status"),
    ]

    DOCKER_PATTERNS = [
        (r"(?:c[oó]mo\s+)?est[aá]n?\s+(?:los\s+)?contenedores", "containers"),
        (r"contenedores\s+(?:activos|corriendo)", "running"),
        (r"docker\s+(?:ps|status)", "containers"),
        (r"logs?\s+(?:del?\s+)?(?:contenedor\s+)?(\w+)", "logs"),
    ]

    TEST_PATTERNS = [
        (r"ejecuta\s+(?:los\s+)?tests?", "run"),
        (r"corre\s+(?:los\s+)?tests?", "run"),
        (r"run\s+tests?", "run"),
    ]

    FILE_PATTERNS = [
        (r"lee\s+(?:el\s+)?(?:archivo\s+)?(.+)", "read"),
        (r"muestra\s+(?:el\s+)?(?:archivo\s+)?(.+)", "read"),
        (r"(?:qu[eé]\s+)?errores\s+(?:hay\s+)?(?:en\s+)?(?:el\s+)?(?:log\s+)?(.+)?", "errors"),
        (r"busca\s+(?:archivos?\s+)?(.+)", "find"),
    ]

    def __init__(self, manager: Optional[DevToolsManager] = None):
        self.manager = manager or DevToolsManager()

    def process_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process a developer-related query."""
        input_lower = user_input.lower().strip()

        # Git queries
        for pattern, query_type in self.GIT_PATTERNS:
            if re.search(pattern, input_lower):
                return (True, self._handle_git(query_type))

        # Docker queries
        for pattern, query_type in self.DOCKER_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                container = match.group(1) if match.lastindex else None
                return (True, self._handle_docker(query_type, container))

        # Test queries
        for pattern, query_type in self.TEST_PATTERNS:
            if re.search(pattern, input_lower):
                return (True, self._handle_tests(query_type))

        # File queries
        for pattern, query_type in self.FILE_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                arg = match.group(1).strip() if match.lastindex and match.group(1) else None
                return (True, self._handle_files(query_type, arg))

        return (False, None)

    def _handle_git(self, query_type: str) -> str:
        if query_type == "uncommitted":
            return self.manager.git.get_uncommitted_changes()
        elif query_type == "status":
            return self.manager.git.get_status()
        elif query_type == "branch":
            return self.manager.git.get_current_branch()
        elif query_type == "commits":
            return self.manager.git.get_recent_commits()
        elif query_type == "diff":
            return self.manager.git.get_diff_summary()
        return "Consulta git no reconocida."

    def _handle_docker(self, query_type: str, container: Optional[str] = None) -> str:
        if query_type == "containers":
            return self.manager.docker.get_containers_status()
        elif query_type == "running":
            return self.manager.docker.get_running_containers()
        elif query_type == "logs" and container:
            return self.manager.docker.get_container_logs(container)
        return "Consulta docker no reconocida."

    def _handle_tests(self, query_type: str) -> str:
        if query_type == "run":
            return self.manager.tests.run_tests()
        return "Consulta de tests no reconocida."

    def _handle_files(self, query_type: str, arg: Optional[str]) -> str:
        if query_type == "read" and arg:
            # Clean up filename
            filename = arg.strip().strip('"\'')
            return self.manager.files.read_file(filename)
        elif query_type == "errors":
            log_file = arg.strip().strip('"\'') if arg else "logs/jarvis.log"
            return self.manager.files.read_log_errors(log_file)
        elif query_type == "find" and arg:
            return self.manager.files.find_files(arg.strip())
        return "Consulta de archivos no reconocida."


# Singleton instances
_manager_instance: Optional[DevToolsManager] = None
_handler_instance: Optional[DevQueryHandler] = None


def get_dev_tools_manager(working_dir: Optional[str] = None) -> DevToolsManager:
    """Get or create the dev tools manager instance."""
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = DevToolsManager(working_dir)

    return _manager_instance


def get_dev_handler() -> DevQueryHandler:
    """Get or create the dev query handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = DevQueryHandler(get_dev_tools_manager())

    return _handler_instance
