"""
Tests for JARVIS System Control module.
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestSystemControl:
    """Tests for SystemControl class."""

    @pytest.fixture
    def control(self):
        """Create a system control instance with temp log."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_path = f.name

        from modules.system_control import SystemControl
        ctrl = SystemControl(log_file=log_path)

        yield ctrl

        if os.path.exists(log_path):
            os.unlink(log_path)

    def test_initialization(self, control):
        """Test control initialization."""
        assert control.log_file.exists() or control.log_file.parent.exists()

    def test_find_application_alias(self, control):
        """Test finding application by alias."""
        # This depends on system, so we test the mechanism
        result = control._find_application("terminal")
        # Result could be konsole, gnome-terminal, xterm, or None
        assert result is None or isinstance(result, str)

    @patch('shutil.which')
    def test_find_application_direct(self, mock_which, control):
        """Test finding application directly."""
        mock_which.return_value = "/usr/bin/firefox"
        result = control._find_application("firefox")
        assert result == "firefox"

    def test_assess_risk_safe(self, control):
        """Test safe command assessment."""
        from modules.system_control import ActionRisk

        safe_commands = [
            "ls -la",
            "pwd",
            "cat file.txt",
            "echo hello",
        ]

        for cmd in safe_commands:
            risk = control._assess_risk(cmd)
            assert risk == ActionRisk.SAFE, f"Should be safe: {cmd}"

    def test_assess_risk_dangerous(self, control):
        """Test dangerous command assessment."""
        from modules.system_control import ActionRisk

        dangerous_commands = [
            "rm -rf folder",
            "sudo apt install",
            "killall process",
            "shutdown now",
        ]

        for cmd in dangerous_commands:
            risk = control._assess_risk(cmd)
            assert risk == ActionRisk.DANGEROUS, f"Should be dangerous: {cmd}"

    def test_assess_risk_forbidden(self, control):
        """Test forbidden command assessment."""
        from modules.system_control import ActionRisk

        forbidden_commands = [
            "rm -rf /",
            "rm -rf /*",
            "dd of=/dev/sda",
        ]

        for cmd in forbidden_commands:
            risk = control._assess_risk(cmd)
            assert risk == ActionRisk.FORBIDDEN, f"Should be forbidden: {cmd}"

    @patch('subprocess.Popen')
    @patch('shutil.which')
    def test_open_application_success(self, mock_which, mock_popen, control):
        """Test opening application successfully."""
        mock_which.return_value = "/usr/bin/firefox"

        result = control.open_application("firefox")

        assert result.success
        assert "firefox" in result.message.lower()
        mock_popen.assert_called_once()

    @patch('shutil.which')
    def test_open_application_not_found(self, mock_which, control):
        """Test opening non-existent application."""
        mock_which.return_value = None

        result = control.open_application("nonexistent_app")

        assert not result.success
        assert "no encontré" in result.message.lower()

    @patch('subprocess.run')
    def test_close_application(self, mock_run, control):
        """Test closing application."""
        mock_run.return_value = MagicMock(returncode=0)

        result = control.close_application("firefox")

        assert result.success or "no encontré" in result.message.lower()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_set_volume_pactl(self, mock_which, mock_run, control):
        """Test setting volume with pactl."""
        mock_which.return_value = "/usr/bin/pactl"
        mock_run.return_value = MagicMock(returncode=0)

        result = control.set_volume(50)

        assert result.success
        assert "50%" in result.message

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_change_volume(self, mock_which, mock_run, control):
        """Test changing volume."""
        mock_which.return_value = "/usr/bin/pactl"
        mock_run.return_value = MagicMock(returncode=0)

        result = control.change_volume(10)

        assert result.success
        assert "subido" in result.message.lower()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_mute(self, mock_which, mock_run, control):
        """Test muting audio."""
        mock_which.return_value = "/usr/bin/pactl"
        mock_run.return_value = MagicMock(returncode=0)

        result = control.mute(True)

        assert result.success
        assert "silenciado" in result.message.lower()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_unmute(self, mock_which, mock_run, control):
        """Test unmuting audio."""
        mock_which.return_value = "/usr/bin/pactl"
        mock_run.return_value = MagicMock(returncode=0)

        result = control.mute(False)

        assert result.success
        assert "activado" in result.message.lower()

    @patch('subprocess.run')
    @patch('shutil.which')
    def test_set_brightness(self, mock_which, mock_run, control):
        """Test setting brightness."""
        mock_which.return_value = "/usr/bin/brightnessctl"
        mock_run.return_value = MagicMock(returncode=0)

        result = control.set_brightness(70)

        assert result.success
        assert "70%" in result.message

    @patch('subprocess.run')
    def test_execute_command_safe(self, mock_run, control):
        """Test executing safe command."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="output",
            stderr=""
        )

        result = control.execute_command("echo hello")

        assert result.success

    def test_execute_command_forbidden(self, control):
        """Test forbidden command is blocked."""
        result = control.execute_command("rm -rf /")

        assert not result.success
        assert "no puedo" in result.message.lower()

    def test_execute_command_dangerous_needs_confirm(self, control):
        """Test dangerous command requires confirmation."""
        result = control.execute_command("rm -rf folder")

        assert not result.success
        assert result.required_confirmation
        assert control.has_pending_confirmation()

    def test_confirm_pending_action(self, control):
        """Test confirming pending action."""
        # First, trigger a dangerous command
        control.execute_command("rm -rf folder")

        # Cancel it
        result = control.confirm_pending_action(False)

        assert result.success
        assert "cancelada" in result.message.lower()
        assert not control.has_pending_confirmation()

    def test_action_logging(self, control):
        """Test action logging."""
        # Perform an action
        control.set_volume(50)

        # Check log file
        assert control.log_file.exists() or len(control.action_history) > 0

    def test_get_recent_actions(self, control):
        """Test getting recent actions."""
        # Perform some actions
        control._log_action("test", "cmd", True, "details",
                           control._assess_risk("ls"))

        recent = control.get_recent_actions(5)
        assert len(recent) >= 1

    def test_get_action_summary(self, control):
        """Test getting action summary."""
        control._log_action("test", "cmd", True, "details",
                           control._assess_risk("ls"))

        summary = control.get_action_summary()
        assert "test" in summary.lower() or "acciones" in summary.lower()


class TestControlQueryHandler:
    """Tests for ControlQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a control query handler."""
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as f:
            log_path = f.name

        from modules.system_control import SystemControl, ControlQueryHandler
        control = SystemControl(log_file=log_path)
        handler = ControlQueryHandler(control)

        yield handler

        if os.path.exists(log_path):
            os.unlink(log_path)

    def test_open_command_patterns(self, handler):
        """Test open command recognition."""
        commands = [
            "abre firefox",
            "abre el terminal",
            "abrir la terminal",
            "ejecuta spotify",
            "lanza chrome",
        ]

        for cmd in commands:
            is_cmd, response = handler.process_command(cmd)
            assert is_cmd, f"Should recognize: {cmd}"

    def test_close_command_patterns(self, handler):
        """Test close command recognition."""
        commands = [
            "cierra firefox",
            "cierra el reproductor",
            "cerrar spotify",
            "termina chrome",
        ]

        for cmd in commands:
            is_cmd, response = handler.process_command(cmd)
            assert is_cmd, f"Should recognize: {cmd}"

    def test_volume_up_command(self, handler):
        """Test volume up command."""
        from modules.system_control import ActionResult

        commands = [
            "sube el volumen",
            "sube volumen",
            "más volumen",
        ]

        with patch.object(handler.control, 'change_volume') as mock_volume:
            mock_volume.return_value = ActionResult(
                success=True, message="Volumen subido.", action_type="volume"
            )
            for cmd in commands:
                is_cmd, response = handler.process_command(cmd)
                assert is_cmd, f"Should recognize: {cmd}"

    def test_volume_down_command(self, handler):
        """Test volume down command."""
        from modules.system_control import ActionResult

        commands = [
            "baja el volumen",
            "baja volumen",
            "menos volumen",
        ]

        with patch.object(handler.control, 'change_volume') as mock_volume:
            mock_volume.return_value = ActionResult(
                success=True, message="Volumen bajado.", action_type="volume"
            )
            for cmd in commands:
                is_cmd, response = handler.process_command(cmd)
                assert is_cmd, f"Should recognize: {cmd}"

    def test_mute_command(self, handler):
        """Test mute command."""
        from modules.system_control import ActionResult

        with patch.object(handler.control, 'mute') as mock_mute:
            mock_mute.return_value = ActionResult(
                success=True, message="Audio silenciado.", action_type="volume"
            )
            is_cmd, response = handler.process_command("silencia")
            assert is_cmd
            assert response is not None

    def test_set_volume_command(self, handler):
        """Test set volume command."""
        from modules.system_control import ActionResult

        commands = [
            "volumen al 50",
            "pon el volumen a 50",
            "pon volumen al 50",
        ]

        with patch.object(handler.control, 'set_volume') as mock_volume:
            mock_volume.return_value = ActionResult(
                success=True, message="Volumen al 50%.", action_type="volume"
            )
            for cmd in commands:
                is_cmd, response = handler.process_command(cmd)
                assert is_cmd, f"Should recognize: {cmd}"

    def test_brightness_commands(self, handler):
        """Test brightness commands."""
        from modules.system_control import ActionResult

        commands = [
            "sube el brillo",
            "baja el brillo",
            "más brillo",
            "menos brillo",
        ]

        with patch.object(handler.control, 'change_brightness') as mock_brightness:
            mock_brightness.return_value = ActionResult(
                success=True, message="Brillo ajustado.", action_type="brightness"
            )
            for cmd in commands:
                is_cmd, response = handler.process_command(cmd)
                assert is_cmd, f"Should recognize: {cmd}"

    def test_non_control_command(self, handler):
        """Test non-control commands pass through."""
        commands = [
            "qué hora es",
            "cuéntame un chiste",
            "cómo está el sistema",
        ]

        for cmd in commands:
            is_cmd, response = handler.process_command(cmd)
            assert not is_cmd, f"Should not recognize: {cmd}"

    def test_confirmation_responses(self, handler):
        """Test confirmation responses."""
        # Set up pending confirmation
        handler.control._pending_confirmation = {
            "command": "rm -rf folder",
            "action": "execute_command"
        }

        # Test "no" response
        is_cmd, response = handler.process_command("no")
        assert is_cmd
        assert "cancelada" in response.lower()


class TestActionResult:
    """Tests for ActionResult dataclass."""

    def test_action_result_creation(self):
        """Test creating action result."""
        from modules.system_control import ActionResult

        result = ActionResult(
            success=True,
            message="Test message",
            action_type="test"
        )

        assert result.success
        assert result.message == "Test message"
        assert result.action_type == "test"

    def test_action_result_with_confirmation(self):
        """Test action result requiring confirmation."""
        from modules.system_control import ActionResult

        result = ActionResult(
            success=False,
            message="Needs confirmation",
            action_type="command",
            required_confirmation=True
        )

        assert not result.success
        assert result.required_confirmation


class TestActionRisk:
    """Tests for ActionRisk enum."""

    def test_risk_levels(self):
        """Test risk level values."""
        from modules.system_control import ActionRisk

        assert ActionRisk.SAFE.value == "safe"
        assert ActionRisk.MODERATE.value == "moderate"
        assert ActionRisk.DANGEROUS.value == "dangerous"
        assert ActionRisk.FORBIDDEN.value == "forbidden"


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_system_control(self):
        """Test get_system_control returns instance."""
        from modules import system_control as sc

        # Reset singleton
        sc._control_instance = None

        control = sc.get_system_control()
        assert control is not None

    def test_get_control_handler(self):
        """Test get_control_handler returns instance."""
        from modules import system_control as sc

        # Reset singletons
        sc._control_instance = None
        sc._handler_instance = None

        handler = sc.get_control_handler()
        assert handler is not None


class TestAppAliases:
    """Tests for application aliases."""

    def test_common_app_aliases_exist(self):
        """Test common app aliases are defined."""
        from modules.system_control import SystemControl

        common_apps = [
            "firefox", "terminal", "archivos", "editor",
            "navegador", "spotify", "vlc"
        ]

        for app in common_apps:
            assert app in SystemControl.APP_ALIASES
