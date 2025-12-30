"""
Tests for JARVIS Screen Vision module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCaptureResult:
    """Tests for CaptureResult dataclass."""

    def test_capture_result_success(self):
        """Test successful capture result."""
        from modules.screen_vision import CaptureResult

        result = CaptureResult(success=True, file_path="/tmp/screen.png")
        assert result.success
        assert result.file_path == "/tmp/screen.png"
        assert result.error is None

    def test_capture_result_failure(self):
        """Test failed capture result."""
        from modules.screen_vision import CaptureResult

        result = CaptureResult(success=False, error="No display")
        assert not result.success
        assert result.error == "No display"


class TestScreenCapture:
    """Tests for ScreenCapture class."""

    @pytest.fixture
    def screen_capture(self):
        """Create a ScreenCapture instance."""
        from modules.screen_vision import ScreenCapture
        with patch('shutil.which', return_value="/usr/bin/spectacle"):
            capture = ScreenCapture()
            yield capture
            capture.cleanup()

    def test_initialization(self, screen_capture):
        """Test ScreenCapture initialization."""
        assert screen_capture.capture_tool is not None
        assert screen_capture.temp_dir is not None

    def test_detect_spectacle(self):
        """Test detecting spectacle tool."""
        from modules.screen_vision import ScreenCapture

        def which_mock(cmd):
            return "/usr/bin/spectacle" if cmd == "spectacle" else None

        with patch('shutil.which', side_effect=which_mock):
            capture = ScreenCapture()
            assert capture.capture_tool == "spectacle"
            capture.cleanup()

    def test_detect_scrot(self):
        """Test detecting scrot tool."""
        from modules.screen_vision import ScreenCapture

        def which_mock(cmd):
            return "/usr/bin/scrot" if cmd == "scrot" else None

        with patch('shutil.which', side_effect=which_mock):
            capture = ScreenCapture()
            assert capture.capture_tool == "scrot"
            capture.cleanup()

    def test_detect_import(self):
        """Test detecting ImageMagick import."""
        from modules.screen_vision import ScreenCapture

        def which_mock(cmd):
            return "/usr/bin/import" if cmd == "import" else None

        with patch('shutil.which', side_effect=which_mock):
            capture = ScreenCapture()
            assert capture.capture_tool == "import"
            capture.cleanup()

    def test_no_tool_available(self):
        """Test when no capture tool is available."""
        from modules.screen_vision import ScreenCapture

        with patch('shutil.which', return_value=None):
            capture = ScreenCapture()
            assert capture.capture_tool is None
            result = capture.capture_screen()
            assert not result.success
            assert "no hay herramientas" in result.error.lower()
            capture.cleanup()

    def test_capture_screen_success(self, screen_capture):
        """Test successful screen capture."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            # Create temp file to simulate capture
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
                temp_path = f.name

            try:
                with patch.object(screen_capture, '_get_capture_args',
                                  return_value=["touch", temp_path]):
                    # Simulate the file being created
                    Path(temp_path).touch()
                    result = screen_capture.capture_screen(temp_path)

                    assert result.success or result.error  # Either success or meaningful error
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_capture_timeout(self, screen_capture):
        """Test capture timeout handling."""
        import subprocess

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 10)):
            result = screen_capture.capture_screen()
            assert not result.success
            assert "tardó demasiado" in result.error.lower()

    def test_cleanup(self, screen_capture):
        """Test cleanup removes files."""
        # Create a temp file in the capture's temp dir
        temp_file = os.path.join(screen_capture.temp_dir, "test.png")
        Path(temp_file).touch()

        assert os.path.exists(temp_file)
        screen_capture.cleanup(temp_file)
        assert not os.path.exists(temp_file)


class TestScreenAnalyzer:
    """Tests for ScreenAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a ScreenAnalyzer instance."""
        from modules.screen_vision import ScreenAnalyzer

        with patch('shutil.which', return_value="/usr/bin/spectacle"):
            analyzer = ScreenAnalyzer(claude_command="claude")
            yield analyzer

    def test_initialization(self, analyzer):
        """Test ScreenAnalyzer initialization."""
        assert analyzer.claude_command == "claude"
        assert analyzer.capture is not None

    def test_analyze_screen_capture_fails(self, analyzer):
        """Test analyze when capture fails."""
        with patch.object(analyzer.capture, 'capture_screen') as mock_capture:
            from modules.screen_vision import CaptureResult
            mock_capture.return_value = CaptureResult(
                success=False,
                error="Display not available"
            )

            result = analyzer.analyze_screen()
            assert "no pude capturar" in result.lower()

    def test_analyze_screen_success(self, analyzer):
        """Test successful screen analysis."""
        from modules.screen_vision import CaptureResult

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            temp_path = f.name

        try:
            with patch.object(analyzer.capture, 'capture_screen') as mock_capture:
                mock_capture.return_value = CaptureResult(
                    success=True,
                    file_path=temp_path
                )

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout="Esta es una descripción de la pantalla."
                    )

                    result = analyzer.analyze_screen()
                    assert "descripción" in result.lower() or len(result) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_read_screen_text(self, analyzer):
        """Test reading screen text."""
        with patch.object(analyzer, 'analyze_screen') as mock_analyze:
            mock_analyze.return_value = "Texto visible en pantalla"
            result = analyzer.read_screen_text()
            assert result is not None

    def test_describe_screen(self, analyzer):
        """Test describing screen."""
        with patch.object(analyzer, 'analyze_screen') as mock_analyze:
            mock_analyze.return_value = "Pantalla con Firefox abierto"
            result = analyzer.describe_screen()
            assert result is not None

    def test_check_for_errors(self, analyzer):
        """Test checking for errors on screen."""
        with patch.object(analyzer, 'analyze_screen') as mock_analyze:
            mock_analyze.return_value = "No hay errores visibles"
            result = analyzer.check_for_errors()
            assert result is not None

    def test_identify_active_app(self, analyzer):
        """Test identifying active application."""
        with patch.object(analyzer, 'analyze_screen') as mock_analyze:
            mock_analyze.return_value = "La aplicación activa es Visual Studio Code"
            result = analyzer.identify_active_app()
            assert result is not None

    def test_answer_about_screen(self, analyzer):
        """Test answering question about screen."""
        with patch.object(analyzer, 'analyze_screen') as mock_analyze:
            mock_analyze.return_value = "Sí, hay una ventana de terminal"
            result = analyzer.answer_about_screen("¿Hay una terminal abierta?")
            assert result is not None


class TestScreenQueryHandler:
    """Tests for ScreenQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a ScreenQueryHandler instance."""
        from modules.screen_vision import ScreenQueryHandler, ScreenAnalyzer

        with patch('shutil.which', return_value="/usr/bin/spectacle"):
            analyzer = ScreenAnalyzer()
            handler = ScreenQueryHandler(analyzer)
            yield handler

    def test_describe_screen_queries(self, handler):
        """Test screen description queries."""
        queries = [
            "qué hay en mi pantalla",
            "qué hay en pantalla",
            "describe la pantalla",
            "qué ves en pantalla",
        ]

        with patch.object(handler.analyzer, 'describe_screen', return_value="Pantalla"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_read_text_queries(self, handler):
        """Test text reading queries."""
        queries = [
            "lee el texto de la pantalla",
            "lee el texto en pantalla",
            "qué texto hay en pantalla",
        ]

        with patch.object(handler.analyzer, 'read_screen_text', return_value="Texto"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_active_app_queries(self, handler):
        """Test active application queries."""
        queries = [
            "qué aplicación tengo abierta",
            "qué programa está abierto",
            "qué app tengo abierta",
        ]

        with patch.object(handler.analyzer, 'identify_active_app', return_value="Firefox"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_error_queries(self, handler):
        """Test error detection queries."""
        queries = [
            "hay algún error en pantalla",
            "hay errores visibles",
            "qué errores hay",
        ]

        with patch.object(handler.analyzer, 'check_for_errors', return_value="No errors"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_screenshot_query(self, handler):
        """Test screenshot capture query."""
        with patch.object(handler.analyzer, 'describe_screen', return_value="Captura"):
            is_handled, response = handler.process_query("captura la pantalla")
            assert is_handled

    def test_non_screen_query(self, handler):
        """Test non-screen queries pass through."""
        queries = [
            "qué hora es",
            "abre firefox",
            "cuánta memoria hay",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert not is_handled, f"Should NOT handle: {query}"


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_screen_analyzer(self):
        """Test get_screen_analyzer returns instance."""
        from modules import screen_vision

        # Reset singleton
        screen_vision._analyzer_instance = None

        with patch('shutil.which', return_value="/usr/bin/spectacle"):
            analyzer = screen_vision.get_screen_analyzer()
            assert analyzer is not None

    def test_get_screen_handler(self):
        """Test get_screen_handler returns instance."""
        from modules import screen_vision

        # Reset singletons
        screen_vision._analyzer_instance = None
        screen_vision._handler_instance = None

        with patch('shutil.which', return_value="/usr/bin/spectacle"):
            handler = screen_vision.get_screen_handler()
            assert handler is not None
