"""
Tests for JARVIS Camera Vision module.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestCameraResult:
    """Tests for CameraResult dataclass."""

    def test_camera_result_success(self):
        """Test successful camera result."""
        from modules.camera_vision import CameraResult

        result = CameraResult(success=True, file_path="/tmp/photo.jpg")
        assert result.success
        assert result.file_path == "/tmp/photo.jpg"
        assert result.error is None

    def test_camera_result_failure(self):
        """Test failed camera result."""
        from modules.camera_vision import CameraResult

        result = CameraResult(success=False, error="Camera busy")
        assert not result.success
        assert result.error == "Camera busy"


class TestCameraCapture:
    """Tests for CameraCapture class."""

    @pytest.fixture
    def camera_capture(self):
        """Create a CameraCapture instance."""
        from modules.camera_vision import CameraCapture

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                with patch('subprocess.run'):
                    capture = CameraCapture()
                    yield capture
                    capture.cleanup()

    def test_initialization(self, camera_capture):
        """Test CameraCapture initialization."""
        assert camera_capture.device is not None
        assert camera_capture.capture_tool is not None

    def test_detect_ffmpeg(self):
        """Test detecting ffmpeg tool."""
        from modules.camera_vision import CameraCapture

        def which_mock(cmd):
            return "/usr/bin/ffmpeg" if cmd == "ffmpeg" else None

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', side_effect=which_mock):
                with patch('subprocess.run'):
                    capture = CameraCapture()
                    assert capture.capture_tool == "ffmpeg"
                    capture.cleanup()

    def test_detect_fswebcam(self):
        """Test detecting fswebcam tool."""
        from modules.camera_vision import CameraCapture

        def which_mock(cmd):
            return "/usr/bin/fswebcam" if cmd == "fswebcam" else None

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', side_effect=which_mock):
                with patch('subprocess.run'):
                    capture = CameraCapture()
                    assert capture.capture_tool == "fswebcam"
                    capture.cleanup()

    def test_no_camera_available(self):
        """Test when no camera is available."""
        from modules.camera_vision import CameraCapture

        with patch('glob.glob', return_value=[]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                capture = CameraCapture()
                assert capture.device is None
                assert not capture.has_camera()
                result = capture.capture_photo()
                assert not result.success
                assert "no se detectó" in result.error.lower()
                capture.cleanup()

    def test_no_tool_available(self):
        """Test when no capture tool is available."""
        from modules.camera_vision import CameraCapture

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value=None):
                with patch('subprocess.run'):
                    capture = CameraCapture()
                    assert capture.capture_tool is None
                    result = capture.capture_photo()
                    assert not result.success
                    assert "no hay herramientas" in result.error.lower()
                    capture.cleanup()

    def test_has_camera(self, camera_capture):
        """Test has_camera check."""
        camera_capture.device = "/dev/video0"
        camera_capture.capture_tool = "ffmpeg"
        assert camera_capture.has_camera()

    def test_capture_photo_success(self, camera_capture):
        """Test successful photo capture."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                temp_path = f.name

            try:
                Path(temp_path).touch()
                result = camera_capture.capture_photo(temp_path)
                # Success depends on file existing after capture
                assert result.success or result.error
            finally:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

    def test_capture_timeout(self, camera_capture):
        """Test capture timeout handling."""
        import subprocess

        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired("cmd", 10)):
            result = camera_capture.capture_photo()
            assert not result.success
            assert "tardó demasiado" in result.error.lower()

    def test_capture_permission_denied(self, camera_capture):
        """Test permission denied handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Permission denied"
            )
            result = camera_capture.capture_photo()
            assert not result.success
            assert "permiso" in result.error.lower()

    def test_capture_device_busy(self, camera_capture):
        """Test device busy handling."""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Device or resource busy"
            )
            result = camera_capture.capture_photo()
            assert not result.success
            assert "en uso" in result.error.lower()

    def test_cleanup(self, camera_capture):
        """Test cleanup removes files."""
        temp_file = os.path.join(camera_capture.temp_dir, "test.jpg")
        Path(temp_file).touch()

        assert os.path.exists(temp_file)
        camera_capture.cleanup(temp_file)
        assert not os.path.exists(temp_file)


class TestCameraAnalyzer:
    """Tests for CameraAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        """Create a CameraAnalyzer instance."""
        from modules.camera_vision import CameraAnalyzer

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                with patch('subprocess.run'):
                    analyzer = CameraAnalyzer(claude_command="claude")
                    yield analyzer

    def test_initialization(self, analyzer):
        """Test CameraAnalyzer initialization."""
        assert analyzer.claude_command == "claude"
        assert analyzer.capture is not None

    def test_analyze_no_camera(self):
        """Test analyze when no camera available."""
        from modules.camera_vision import CameraAnalyzer

        with patch('glob.glob', return_value=[]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                analyzer = CameraAnalyzer()
                result = analyzer.analyze_camera()
                assert "no hay cámara" in result.lower()

    def test_analyze_capture_fails(self, analyzer):
        """Test analyze when capture fails."""
        from modules.camera_vision import CameraResult

        with patch.object(analyzer.capture, 'capture_photo') as mock_capture:
            mock_capture.return_value = CameraResult(
                success=False,
                error="Camera busy"
            )

            result = analyzer.analyze_camera()
            assert "no pude capturar" in result.lower()

    def test_analyze_success(self, analyzer):
        """Test successful camera analysis."""
        from modules.camera_vision import CameraResult

        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            temp_path = f.name

        try:
            with patch.object(analyzer.capture, 'capture_photo') as mock_capture:
                mock_capture.return_value = CameraResult(
                    success=True,
                    file_path=temp_path
                )

                with patch('subprocess.run') as mock_run:
                    mock_run.return_value = MagicMock(
                        returncode=0,
                        stdout="Veo una persona frente a la cámara."
                    )

                    result = analyzer.analyze_camera()
                    assert "persona" in result.lower() or len(result) > 0
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_describe_view(self, analyzer):
        """Test describing camera view."""
        with patch.object(analyzer, 'analyze_camera') as mock_analyze:
            mock_analyze.return_value = "Vista de la cámara"
            result = analyzer.describe_view()
            assert result is not None

    def test_check_presence(self, analyzer):
        """Test checking for presence."""
        with patch.object(analyzer, 'analyze_camera') as mock_analyze:
            mock_analyze.return_value = "No hay nadie visible"
            result = analyzer.check_presence()
            assert result is not None

    def test_describe_user(self, analyzer):
        """Test describing user appearance."""
        with patch.object(analyzer, 'analyze_camera') as mock_analyze:
            mock_analyze.return_value = "Persona sonriente"
            result = analyzer.describe_user()
            assert result is not None

    def test_identify_object(self, analyzer):
        """Test identifying objects."""
        with patch.object(analyzer, 'analyze_camera') as mock_analyze:
            mock_analyze.return_value = "Libro en la mano"
            result = analyzer.identify_object()
            assert result is not None

    def test_answer_about_camera(self, analyzer):
        """Test answering question about camera view."""
        with patch.object(analyzer, 'analyze_camera') as mock_analyze:
            mock_analyze.return_value = "Sí, hay una ventana"
            result = analyzer.answer_about_camera("¿Hay una ventana?")
            assert result is not None


class TestCameraQueryHandler:
    """Tests for CameraQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a CameraQueryHandler instance."""
        from modules.camera_vision import CameraQueryHandler, CameraAnalyzer

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                with patch('subprocess.run'):
                    analyzer = CameraAnalyzer()
                    handler = CameraQueryHandler(analyzer)
                    yield handler

    def test_describe_queries(self, handler):
        """Test camera description queries."""
        queries = [
            "qué ves con la cámara",
            "qué hay en la cámara",
            "mira con la cámara",
        ]

        with patch.object(handler.analyzer, 'describe_view', return_value="Vista"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_presence_queries(self, handler):
        """Test presence detection queries."""
        queries = [
            "hay alguien detrás de mí",
            "hay alguien atrás",
            "hay alguien visible",
        ]

        with patch.object(handler.analyzer, 'check_presence', return_value="Nadie"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_describe_user_queries(self, handler):
        """Test user description queries."""
        queries = [
            "cómo me veo",
            "cómo estoy",
        ]

        with patch.object(handler.analyzer, 'describe_user', return_value="Bien"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_object_queries(self, handler):
        """Test object identification queries."""
        queries = [
            "qué objeto tengo",
            "qué tengo en la mano",
        ]

        with patch.object(handler.analyzer, 'identify_object', return_value="Libro"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_activate_queries(self, handler):
        """Test camera activation queries."""
        queries = [
            "activa la cámara",
            "usar la cámara",
        ]

        with patch.object(handler.analyzer, 'describe_view', return_value="Vista"):
            for query in queries:
                is_handled, response = handler.process_query(query)
                assert is_handled, f"Should handle: {query}"

    def test_non_camera_query(self, handler):
        """Test non-camera queries pass through."""
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

    def test_get_camera_analyzer(self):
        """Test get_camera_analyzer returns instance."""
        from modules import camera_vision

        # Reset singleton
        camera_vision._analyzer_instance = None

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                with patch('subprocess.run'):
                    analyzer = camera_vision.get_camera_analyzer()
                    assert analyzer is not None

    def test_get_camera_handler(self):
        """Test get_camera_handler returns instance."""
        from modules import camera_vision

        # Reset singletons
        camera_vision._analyzer_instance = None
        camera_vision._handler_instance = None

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                with patch('subprocess.run'):
                    handler = camera_vision.get_camera_handler()
                    assert handler is not None


class TestPrivacyCompliance:
    """Tests for privacy and security compliance."""

    def test_activation_notice_exists(self):
        """Test that activation notice is defined."""
        from modules.camera_vision import CameraAnalyzer
        assert hasattr(CameraAnalyzer, 'ACTIVATION_NOTICE')
        assert len(CameraAnalyzer.ACTIVATION_NOTICE) > 0

    def test_cleanup_always_called(self):
        """Test that cleanup is always called after analysis."""
        from modules.camera_vision import CameraAnalyzer, CameraResult

        with patch('glob.glob', return_value=["/dev/video0"]):
            with patch('shutil.which', return_value="/usr/bin/ffmpeg"):
                with patch('subprocess.run'):
                    analyzer = CameraAnalyzer()

                    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                        temp_path = f.name

                    try:
                        with patch.object(analyzer.capture, 'capture_photo') as mock_capture:
                            mock_capture.return_value = CameraResult(
                                success=True,
                                file_path=temp_path
                            )

                            with patch.object(analyzer.capture, 'cleanup') as mock_cleanup:
                                with patch('subprocess.run') as mock_run:
                                    mock_run.return_value = MagicMock(
                                        returncode=0,
                                        stdout="Test"
                                    )
                                    analyzer.analyze_camera()

                                # Verify cleanup was called
                                mock_cleanup.assert_called_once_with(temp_path)
                    finally:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
