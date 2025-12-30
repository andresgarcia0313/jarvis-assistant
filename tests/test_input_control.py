"""
Tests for JARVIS Input Control module.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestActionTypes:
    """Tests for ActionType and related dataclasses."""

    def test_action_type_enum(self):
        """Test ActionType enum values."""
        from modules.input_control import ActionType

        assert ActionType.MOUSE_MOVE.value == "mouse_move"
        assert ActionType.MOUSE_CLICK.value == "mouse_click"
        assert ActionType.KEY_TYPE.value == "key_type"

    def test_input_action_creation(self):
        """Test InputAction dataclass."""
        from modules.input_control import InputAction, ActionType

        action = InputAction(
            action_type=ActionType.MOUSE_CLICK,
            description="hacer click",
            params={"button": "left"}
        )

        assert action.action_type == ActionType.MOUSE_CLICK
        assert action.description == "hacer click"
        assert not action.confirmed

    def test_action_result(self):
        """Test ActionResult dataclass."""
        from modules.input_control import ActionResult

        result = ActionResult(success=True, message="Done")
        assert result.success
        assert result.message == "Done"


class TestInputController:
    """Tests for InputController class."""

    @pytest.fixture
    def controller(self):
        """Create an InputController instance."""
        from modules.input_control import InputController

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = InputController(demo_mode=True)
            yield controller

    def test_initialization(self, controller):
        """Test InputController initialization."""
        assert controller.demo_mode
        assert controller.tool is not None

    def test_detect_xdotool(self):
        """Test detecting xdotool."""
        from modules.input_control import InputController

        def which_mock(cmd):
            return "/usr/bin/xdotool" if cmd == "xdotool" else None

        with patch('shutil.which', side_effect=which_mock):
            controller = InputController()
            assert controller.tool == "xdotool"

    def test_no_tool_available(self):
        """Test when no tool is available."""
        from modules.input_control import InputController

        with patch('shutil.which', return_value=None):
            controller = InputController()
            assert not controller.is_available()

    def test_stop_and_reset(self, controller):
        """Test stop and reset functionality."""
        controller.stop()
        assert controller._stopped

        controller.reset()
        assert not controller._stopped

    def test_demo_mode_logging(self, controller):
        """Test that demo mode logs but doesn't execute."""
        result = controller.move_mouse(100, 200)
        assert result.success
        assert "Demo" in result.message
        assert len(controller.action_log) > 0

    def test_move_mouse_to_region(self, controller):
        """Test moving mouse to named region."""
        regions = ["centro", "arriba", "abajo", "izquierda", "derecha"]

        for region in regions:
            result = controller.move_mouse_to_region(region)
            assert result.success, f"Should handle region: {region}"

    def test_move_mouse_invalid_region(self, controller):
        """Test moving mouse to invalid region."""
        result = controller.move_mouse_to_region("invalid_place")
        assert not result.success

    def test_click_types(self, controller):
        """Test different click types."""
        # Left click
        result = controller.click("left")
        assert result.success

        # Right click
        result = controller.click("derecho")
        assert result.success

        # Double click
        result = controller.click("left", count=2)
        assert result.success

    def test_scroll(self, controller):
        """Test scroll functionality."""
        result = controller.scroll("abajo")
        assert result.success

        result = controller.scroll("arriba")
        assert result.success

    def test_scroll_invalid_direction(self, controller):
        """Test scroll with invalid direction."""
        result = controller.scroll("sideways")
        assert not result.success

    def test_type_text(self, controller):
        """Test typing text."""
        result = controller.type_text("Hello World")
        assert result.success

    def test_press_key(self, controller):
        """Test pressing a single key."""
        result = controller.press_key("Return")
        assert result.success

    def test_press_combo(self, controller):
        """Test pressing key combination."""
        result = controller.press_combo("control", "alt", "t")
        assert result.success

    def test_key_mappings(self, controller):
        """Test key name mappings."""
        from modules.input_control import InputController

        assert InputController.KEY_MAPPINGS["control"] == "ctrl"
        assert InputController.KEY_MAPPINGS["enter"] == "Return"
        assert InputController.KEY_MAPPINGS["espacio"] == "space"

    def test_stopped_prevents_actions(self, controller):
        """Test that stopped state prevents actions."""
        controller._stopped = True
        controller.demo_mode = False

        result = controller.move_mouse(100, 100)
        assert not result.success
        assert "detenidas" in result.message.lower()


class TestSafeInputController:
    """Tests for SafeInputController class."""

    @pytest.fixture
    def safe_controller(self):
        """Create a SafeInputController instance."""
        from modules.input_control import SafeInputController

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = SafeInputController(demo_mode=True)
            yield controller

    def test_initialization(self, safe_controller):
        """Test SafeInputController initialization."""
        assert safe_controller.is_available()
        assert safe_controller.pending_action is None

    def test_safety_word_detection(self, safe_controller):
        """Test safety word detection."""
        safety_words = ["alto", "para", "stop", "detente", "cancelar"]

        for word in safety_words:
            assert safe_controller.is_safety_word(word)

        assert not safe_controller.is_safety_word("continuar")

    def test_emergency_stop(self, safe_controller):
        """Test emergency stop."""
        from modules.input_control import InputAction, ActionType

        # Set up pending action
        safe_controller.pending_action = InputAction(
            action_type=ActionType.MOUSE_CLICK,
            description="test",
            params={}
        )

        safe_controller.emergency_stop()

        assert safe_controller.pending_action is None
        assert safe_controller.controller._stopped

    def test_prepare_action(self, safe_controller):
        """Test preparing an action."""
        from modules.input_control import InputAction, ActionType

        action = InputAction(
            action_type=ActionType.MOUSE_CLICK,
            description="hacer click",
            params={"button": "left"}
        )

        message = safe_controller.prepare_action(action)

        assert "hacer click" in message
        assert "procedo" in message.lower()
        assert safe_controller.pending_action == action

    def test_confirm_and_execute(self, safe_controller):
        """Test confirming and executing action."""
        from modules.input_control import InputAction, ActionType

        action = InputAction(
            action_type=ActionType.MOUSE_CLICK,
            description="hacer click",
            params={"button": "left"}
        )

        safe_controller.prepare_action(action)
        result = safe_controller.confirm_and_execute()

        assert result.success
        assert safe_controller.pending_action is None

    def test_cancel_pending(self, safe_controller):
        """Test canceling pending action."""
        from modules.input_control import InputAction, ActionType

        action = InputAction(
            action_type=ActionType.MOUSE_MOVE,
            description="mover mouse",
            params={"region": "centro"}
        )

        safe_controller.prepare_action(action)
        message = safe_controller.cancel_pending()

        assert "Cancelado" in message
        assert safe_controller.pending_action is None

    def test_action_limit(self, safe_controller):
        """Test action limit per sequence."""
        from modules.input_control import InputAction, ActionType

        safe_controller.actions_in_sequence = safe_controller.MAX_ACTIONS_PER_SEQUENCE

        action = InputAction(
            action_type=ActionType.MOUSE_CLICK,
            description="test",
            params={}
        )

        message = safe_controller.prepare_action(action)
        assert "límite" in message.lower()


class TestInputQueryHandler:
    """Tests for InputQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create an InputQueryHandler instance."""
        from modules.input_control import InputQueryHandler, SafeInputController

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = SafeInputController(demo_mode=True)
            handler = InputQueryHandler(controller)
            yield handler

    def test_mouse_move_queries(self, handler):
        """Test mouse movement queries."""
        queries = [
            "mueve el mouse a la derecha",
            "pon el mouse en el centro",
            "mouse arriba",
        ]

        for query in queries:
            # Reset state between queries
            handler.awaiting_confirmation = False
            handler.controller.pending_action = None

            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"
            assert "procedo" in response.lower()

    def test_click_queries(self, handler):
        """Test click queries."""
        queries = [
            ("haz click", "click"),
            ("click derecho", "derecho"),
            ("doble click", "doble"),
        ]

        for query, expected in queries:
            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"

    def test_scroll_queries(self, handler):
        """Test scroll queries."""
        queries = [
            "baja la página",
            "sube",
            "scroll abajo",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"

    def test_type_queries(self, handler):
        """Test typing queries."""
        queries = [
            "escribe: Hola mundo",
            "teclea: Test",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"

    def test_key_combo_queries(self, handler):
        """Test key combination queries."""
        queries = [
            "presiona control alt t",
            "pulsa escape",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"

    def test_safety_word_stops_all(self, handler):
        """Test that safety words stop all actions."""
        # First prepare an action
        handler.process_query("haz click")

        # Then say safety word
        is_handled, response = handler.process_query("alto")

        assert is_handled
        assert "detenidas" in response.lower()
        assert not handler.awaiting_confirmation

    def test_confirmation_flow(self, handler):
        """Test confirmation flow."""
        # Prepare action
        is_handled, response = handler.process_query("haz click")
        assert is_handled
        assert handler.awaiting_confirmation

        # Confirm
        is_handled, response = handler.process_query("sí")
        assert is_handled
        assert not handler.awaiting_confirmation

    def test_cancellation_flow(self, handler):
        """Test cancellation flow."""
        # Prepare action
        handler.process_query("haz click")
        assert handler.awaiting_confirmation

        # Cancel
        is_handled, response = handler.process_query("no")
        assert is_handled
        assert "Cancelado" in response
        assert not handler.awaiting_confirmation

    def test_reset_command(self, handler):
        """Test reset command."""
        is_handled, response = handler.process_query("reset")
        assert is_handled
        assert "reiniciado" in response.lower()

    def test_non_input_query(self, handler):
        """Test non-input queries pass through."""
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

    def test_get_input_controller(self):
        """Test get_input_controller returns instance."""
        from modules import input_control

        # Reset singleton
        input_control._controller_instance = None

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = input_control.get_input_controller()
            assert controller is not None

    def test_get_input_handler(self):
        """Test get_input_handler returns instance."""
        from modules import input_control

        # Reset singletons
        input_control._controller_instance = None
        input_control._handler_instance = None

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            handler = input_control.get_input_handler()
            assert handler is not None


class TestSecurityFeatures:
    """Tests for security features."""

    def test_confirmation_required(self):
        """Test that all actions require confirmation."""
        from modules.input_control import InputQueryHandler, SafeInputController

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = SafeInputController(demo_mode=True)
            handler = InputQueryHandler(controller)

            # Any action should require confirmation
            is_handled, response = handler.process_query("haz click")

            assert is_handled
            assert "procedo" in response.lower()
            assert handler.awaiting_confirmation

    def test_action_logging(self):
        """Test that actions are logged."""
        from modules.input_control import InputController

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = InputController(demo_mode=True)

            controller.click("left")

            assert len(controller.action_log) > 0
            assert "click" in controller.action_log[0].lower()

    def test_demo_mode_no_execution(self):
        """Test that demo mode doesn't execute real actions."""
        from modules.input_control import InputController

        with patch('shutil.which', return_value="/usr/bin/xdotool"):
            controller = InputController(demo_mode=True)

            with patch('subprocess.run') as mock_run:
                controller.click("left")

                # subprocess.run should not be called in demo mode
                mock_run.assert_not_called()
