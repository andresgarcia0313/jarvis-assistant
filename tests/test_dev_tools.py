"""
Tests for JARVIS Developer Tools module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCommandResult:
    """Tests for CommandResult dataclass."""

    def test_command_result_success(self):
        """Test successful command result."""
        from modules.dev_tools import CommandResult

        result = CommandResult(success=True, output="output text")
        assert result.success
        assert result.output == "output text"
        assert result.error is None

    def test_command_result_failure(self):
        """Test failed command result."""
        from modules.dev_tools import CommandResult

        result = CommandResult(success=False, output="", error="error message")
        assert not result.success
        assert result.error == "error message"


class TestGitTools:
    """Tests for GitTools class."""

    @pytest.fixture
    def git_tools(self):
        """Create a GitTools instance."""
        from modules.dev_tools import GitTools
        return GitTools()

    def test_initialization(self, git_tools):
        """Test GitTools initialization."""
        assert git_tools.working_dir is not None

    def test_initialization_with_dir(self):
        """Test GitTools with custom directory."""
        from modules.dev_tools import GitTools
        git = GitTools(working_dir="/tmp")
        assert git.working_dir == "/tmp"

    def test_is_git_repo(self, git_tools):
        """Test checking if directory is git repo."""
        with patch.object(git_tools, '_run_git') as mock_run:
            mock_run.return_value = MagicMock(success=True)
            assert git_tools.is_git_repo()

            mock_run.return_value = MagicMock(success=False)
            assert not git_tools.is_git_repo()

    def test_get_status_not_repo(self, git_tools):
        """Test get_status when not in a repo."""
        with patch.object(git_tools, 'is_git_repo', return_value=False):
            result = git_tools.get_status()
            assert "no es un repositorio" in result.lower()

    def test_get_status_clean(self, git_tools):
        """Test get_status with clean repo."""
        with patch.object(git_tools, 'is_git_repo', return_value=True):
            with patch.object(git_tools, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(success=True, output="")
                result = git_tools.get_status()
                assert "limpio" in result.lower()

    def test_get_status_with_changes(self, git_tools):
        """Test get_status with changes."""
        with patch.object(git_tools, 'is_git_repo', return_value=True):
            with patch.object(git_tools, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(
                    success=True,
                    output=" M file1.py\n M file2.py\n?? newfile.py"
                )
                result = git_tools.get_status()
                assert "modificado" in result.lower()
                assert "nuevo" in result.lower()

    def test_get_current_branch(self, git_tools):
        """Test getting current branch."""
        with patch.object(git_tools, 'is_git_repo', return_value=True):
            with patch.object(git_tools, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(success=True, output="main")
                result = git_tools.get_current_branch()
                assert "main" in result

    def test_get_current_branch_not_repo(self, git_tools):
        """Test getting branch when not in repo."""
        with patch.object(git_tools, 'is_git_repo', return_value=False):
            result = git_tools.get_current_branch()
            assert "no es un repositorio" in result.lower()

    def test_get_recent_commits(self, git_tools):
        """Test getting recent commits."""
        with patch.object(git_tools, 'is_git_repo', return_value=True):
            with patch.object(git_tools, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(
                    success=True,
                    output="abc123 First commit\ndef456 Second commit"
                )
                result = git_tools.get_recent_commits()
                assert "commit" in result.lower()
                assert "First commit" in result

    def test_get_uncommitted_changes(self, git_tools):
        """Test getting uncommitted changes."""
        with patch.object(git_tools, 'is_git_repo', return_value=True):
            with patch.object(git_tools, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(
                    success=True,
                    output=" M modified.py\n?? new.py"
                )
                result = git_tools.get_uncommitted_changes()
                assert "modificados" in result.lower() or "modified" in result.lower()

    def test_get_diff_summary(self, git_tools):
        """Test getting diff summary."""
        with patch.object(git_tools, 'is_git_repo', return_value=True):
            with patch.object(git_tools, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(
                    success=True,
                    output="file.py | 10 ++++------\n 1 file changed"
                )
                result = git_tools.get_diff_summary()
                assert "diferencias" in result.lower()

    def test_run_git_no_git_installed(self, git_tools):
        """Test running git when not installed."""
        with patch('shutil.which', return_value=None):
            from modules.dev_tools import GitTools
            git = GitTools()
            result = git._run_git("status")
            assert not result.success
            assert "no está instalado" in result.error.lower()


class TestDockerTools:
    """Tests for DockerTools class."""

    @pytest.fixture
    def docker_tools(self):
        """Create a DockerTools instance."""
        from modules.dev_tools import DockerTools
        return DockerTools()

    def test_initialization(self, docker_tools):
        """Test DockerTools initialization."""
        assert hasattr(docker_tools, 'has_docker')

    def test_get_containers_status_no_docker(self):
        """Test containers status when docker not installed."""
        with patch('shutil.which', return_value=None):
            from modules.dev_tools import DockerTools
            docker = DockerTools()
            result = docker.get_containers_status()
            assert "no está instalado" in result.lower()

    def test_get_containers_status_empty(self, docker_tools):
        """Test containers status with no containers."""
        with patch.object(docker_tools, '_run_docker') as mock_run:
            mock_run.return_value = MagicMock(success=True, output="")
            docker_tools.has_docker = True
            result = docker_tools.get_containers_status()
            assert "no hay contenedores" in result.lower()

    def test_get_containers_status_with_containers(self, docker_tools):
        """Test containers status with containers."""
        with patch.object(docker_tools, '_run_docker') as mock_run:
            mock_run.return_value = MagicMock(
                success=True,
                output="container1\tUp 2 hours\timage1\ncontainer2\tExited\timage2"
            )
            docker_tools.has_docker = True
            result = docker_tools.get_containers_status()
            assert "activo" in result.lower()

    def test_get_running_containers(self, docker_tools):
        """Test getting running containers."""
        with patch.object(docker_tools, '_run_docker') as mock_run:
            mock_run.return_value = MagicMock(
                success=True,
                output="web: nginx\ndb: postgres"
            )
            docker_tools.has_docker = True
            result = docker_tools.get_running_containers()
            assert "activos" in result.lower()

    def test_get_container_logs(self, docker_tools):
        """Test getting container logs."""
        with patch.object(docker_tools, '_run_docker') as mock_run:
            mock_run.return_value = MagicMock(
                success=True,
                output="Log line 1\nLog line 2"
            )
            docker_tools.has_docker = True
            result = docker_tools.get_container_logs("mycontainer")
            assert "líneas" in result.lower()


class TestTestRunner:
    """Tests for TestRunner class."""

    @pytest.fixture
    def test_runner(self):
        """Create a TestRunner instance."""
        from modules.dev_tools import TestRunner
        with tempfile.TemporaryDirectory() as tmpdir:
            yield TestRunner(working_dir=tmpdir), tmpdir

    def test_initialization(self, test_runner):
        """Test TestRunner initialization."""
        runner, tmpdir = test_runner
        assert runner.working_dir == tmpdir

    def test_detect_pytest(self, test_runner):
        """Test detecting pytest framework."""
        runner, tmpdir = test_runner
        # Create pytest.ini
        (Path(tmpdir) / "pytest.ini").touch()

        with patch('shutil.which', return_value="/usr/bin/pytest"):
            framework = runner.detect_test_framework()
            assert framework == "pytest"

    def test_detect_npm_test(self, test_runner):
        """Test detecting npm test."""
        runner, tmpdir = test_runner
        import json

        pkg = {"scripts": {"test": "jest"}}
        with open(Path(tmpdir) / "package.json", 'w') as f:
            json.dump(pkg, f)

        framework = runner.detect_test_framework()
        assert framework == "npm test"

    def test_detect_go_test(self, test_runner):
        """Test detecting go test."""
        runner, tmpdir = test_runner
        (Path(tmpdir) / "main_test.go").touch()

        framework = runner.detect_test_framework()
        assert framework == "go test"

    def test_detect_cargo_test(self, test_runner):
        """Test detecting cargo test."""
        runner, tmpdir = test_runner
        (Path(tmpdir) / "Cargo.toml").touch()

        framework = runner.detect_test_framework()
        assert framework == "cargo test"

    def test_detect_no_framework(self, test_runner):
        """Test when no framework detected."""
        runner, tmpdir = test_runner
        framework = runner.detect_test_framework()
        assert framework is None

    def test_run_tests_no_framework(self, test_runner):
        """Test running tests when no framework detected."""
        runner, tmpdir = test_runner
        result = runner.run_tests()
        assert "no pude detectar" in result.lower()

    def test_run_tests_success(self, test_runner):
        """Test running tests successfully."""
        runner, tmpdir = test_runner

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="5 passed in 0.5s",
                stderr=""
            )
            result = runner.run_tests(framework="pytest")
            assert "pasaron" in result.lower() or "correctamente" in result.lower()

    def test_run_tests_failure(self, test_runner):
        """Test running tests with failures."""
        runner, tmpdir = test_runner

        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="2 failed, 3 passed",
                stderr=""
            )
            result = runner.run_tests(framework="pytest")
            assert "fallaron" in result.lower()


class TestFileReader:
    """Tests for FileReader class."""

    @pytest.fixture
    def file_reader(self):
        """Create a FileReader instance."""
        from modules.dev_tools import FileReader
        with tempfile.TemporaryDirectory() as tmpdir:
            yield FileReader(working_dir=tmpdir), tmpdir

    def test_initialization(self, file_reader):
        """Test FileReader initialization."""
        reader, tmpdir = file_reader
        assert reader.working_dir == tmpdir

    def test_read_file_exists(self, file_reader):
        """Test reading an existing file."""
        reader, tmpdir = file_reader

        # Create a test file
        test_file = Path(tmpdir) / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")

        result = reader.read_file("test.txt")
        assert "Line 1" in result
        assert "Line 2" in result

    def test_read_file_not_exists(self, file_reader):
        """Test reading a non-existent file."""
        reader, tmpdir = file_reader

        result = reader.read_file("nonexistent.txt")
        assert "no encontré" in result.lower()

    def test_read_file_truncation(self, file_reader):
        """Test file truncation for long files."""
        reader, tmpdir = file_reader

        # Create a file with many lines
        test_file = Path(tmpdir) / "long.txt"
        test_file.write_text("\n".join(f"Line {i}" for i in range(100)))

        result = reader.read_file("long.txt", lines=10)
        assert "mostrando" in result.lower() or "primeras" in result.lower()

    def test_read_log_errors(self, file_reader):
        """Test reading errors from log file."""
        reader, tmpdir = file_reader

        # Create a log file with errors
        log_file = Path(tmpdir) / "app.log"
        log_file.write_text(
            "INFO: Started\n"
            "ERROR: Something went wrong\n"
            "DEBUG: Details\n"
            "FATAL: Critical failure\n"
        )

        result = reader.read_log_errors("app.log")
        assert "error" in result.lower()
        assert "Something went wrong" in result or "errores encontrados" in result.lower()

    def test_read_log_no_errors(self, file_reader):
        """Test reading log with no errors."""
        reader, tmpdir = file_reader

        log_file = Path(tmpdir) / "clean.log"
        log_file.write_text("INFO: All good\nDEBUG: Working fine")

        result = reader.read_log_errors("clean.log")
        assert "no encontré errores" in result.lower()

    def test_find_files(self, file_reader):
        """Test finding files by pattern."""
        reader, tmpdir = file_reader

        # Create some test files
        (Path(tmpdir) / "test1.py").touch()
        (Path(tmpdir) / "test2.py").touch()
        (Path(tmpdir) / "other.txt").touch()

        result = reader.find_files("*.py")
        assert "test1.py" in result
        assert "test2.py" in result
        assert "other.txt" not in result

    def test_find_files_no_match(self, file_reader):
        """Test finding files with no matches."""
        reader, tmpdir = file_reader

        result = reader.find_files("*.xyz")
        assert "no encontré" in result.lower()


class TestDevToolsManager:
    """Tests for DevToolsManager class."""

    @pytest.fixture
    def manager(self):
        """Create a DevToolsManager instance."""
        from modules.dev_tools import DevToolsManager
        return DevToolsManager()

    def test_initialization(self, manager):
        """Test DevToolsManager initialization."""
        assert manager.git is not None
        assert manager.docker is not None
        assert manager.tests is not None
        assert manager.files is not None

    def test_set_working_dir_valid(self, manager):
        """Test setting valid working directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = manager.set_working_dir(tmpdir)
            assert "cambiado" in result.lower()
            assert manager.working_dir == tmpdir

    def test_set_working_dir_invalid(self, manager):
        """Test setting invalid working directory."""
        result = manager.set_working_dir("/nonexistent/path/12345")
        assert "no existe" in result.lower()


class TestDevQueryHandler:
    """Tests for DevQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a DevQueryHandler instance."""
        from modules.dev_tools import DevToolsManager, DevQueryHandler
        manager = DevToolsManager()
        return DevQueryHandler(manager)

    def test_git_status_queries(self, handler):
        """Test git status queries."""
        queries = [
            "estado del repositorio",
            "git status",
            "estado del git",
        ]

        with patch.object(handler.manager.git, 'is_git_repo', return_value=True):
            with patch.object(handler.manager.git, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(success=True, output="")

                for query in queries:
                    is_handled, response = handler.process_query(query)
                    assert is_handled, f"Should handle: {query}"

    def test_git_branch_queries(self, handler):
        """Test git branch queries."""
        queries = [
            "qué rama estoy",
            "rama actual",
        ]

        with patch.object(handler.manager.git, 'is_git_repo', return_value=True):
            with patch.object(handler.manager.git, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(success=True, output="main")

                for query in queries:
                    is_handled, response = handler.process_query(query)
                    assert is_handled, f"Should handle: {query}"

    def test_git_commits_queries(self, handler):
        """Test git commits queries."""
        queries = [
            "últimos commits",
            "último commit",
        ]

        with patch.object(handler.manager.git, 'is_git_repo', return_value=True):
            with patch.object(handler.manager.git, '_run_git') as mock_run:
                mock_run.return_value = MagicMock(
                    success=True,
                    output="abc123 commit msg"
                )

                for query in queries:
                    is_handled, response = handler.process_query(query)
                    assert is_handled, f"Should handle: {query}"

    def test_docker_queries(self, handler):
        """Test docker queries."""
        queries = [
            "cómo están los contenedores",
            "docker status",
            "contenedores activos",
        ]

        handler.manager.docker.has_docker = True
        with patch.object(handler.manager.docker, '_run_docker') as mock_run:
            mock_run.return_value = MagicMock(success=True, output="")

            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_test_queries(self, handler):
        """Test test execution queries."""
        queries = [
            "ejecuta los tests",
            "corre los tests",
            "run tests",
        ]

        for query in queries:
            with patch.object(handler.manager.tests, 'detect_test_framework', return_value=None):
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_file_read_queries(self, handler):
        """Test file read queries."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("test content")
            temp_path = f.name

        try:
            handler.manager.files.working_dir = os.path.dirname(temp_path)

            is_handled, response = handler.process_query(
                f"lee el archivo {os.path.basename(temp_path)}"
            )
            assert is_handled
        finally:
            os.unlink(temp_path)

    def test_file_find_queries(self, handler):
        """Test file find queries."""
        is_handled, response = handler.process_query("busca archivos *.py")
        assert is_handled

    def test_non_dev_query(self, handler):
        """Test non-dev queries pass through."""
        queries = [
            "qué hora es",
            "hola jarvis",
            "abre firefox",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert not is_handled, f"Should NOT handle: {query}"


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_dev_tools_manager(self):
        """Test get_dev_tools_manager returns instance."""
        from modules import dev_tools

        # Reset singleton
        dev_tools._manager_instance = None

        manager = dev_tools.get_dev_tools_manager()
        assert manager is not None

    def test_get_dev_handler(self):
        """Test get_dev_handler returns instance."""
        from modules import dev_tools

        # Reset singletons
        dev_tools._manager_instance = None
        dev_tools._handler_instance = None

        handler = dev_tools.get_dev_handler()
        assert handler is not None
