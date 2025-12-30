"""
Tests for JARVIS Visual Automation module.
"""

import pytest
from unittest.mock import patch, MagicMock


class TestTaskStatus:
    """Tests for TaskStatus enum."""

    def test_status_values(self):
        """Test TaskStatus enum values."""
        from modules.visual_automation import TaskStatus

        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.EXECUTING.value == "executing"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestAutomationStep:
    """Tests for AutomationStep dataclass."""

    def test_step_creation(self):
        """Test creating an automation step."""
        from modules.visual_automation import AutomationStep

        step = AutomationStep(
            description="Test step",
            action_type="click",
            params={"button": "left"}
        )

        assert step.description == "Test step"
        assert step.action_type == "click"
        assert not step.completed
        assert step.result is None


class TestAutomationTask:
    """Tests for AutomationTask dataclass."""

    def test_task_creation(self):
        """Test creating an automation task."""
        from modules.visual_automation import AutomationTask, TaskStatus

        task = AutomationTask(description="Open browser and search")

        assert task.description == "Open browser and search"
        assert task.status == TaskStatus.PENDING
        assert task.steps == []
        assert task.current_step == 0


class TestVisualAutomation:
    """Tests for VisualAutomation class."""

    @pytest.fixture
    def automation(self):
        """Create a VisualAutomation instance."""
        from modules.visual_automation import VisualAutomation

        automation = VisualAutomation()
        yield automation
        automation.reset()

    def test_initialization(self, automation):
        """Test VisualAutomation initialization."""
        assert automation.current_task is None
        assert not automation._cancelled

    def test_cancel(self, automation):
        """Test cancelling automation."""
        from modules.visual_automation import AutomationTask, TaskStatus

        automation.current_task = AutomationTask(description="test")
        automation.cancel()

        assert automation._cancelled
        assert automation.current_task.status == TaskStatus.CANCELLED

    def test_reset(self, automation):
        """Test resetting automation."""
        automation._cancelled = True
        automation.reset()

        assert not automation._cancelled
        assert automation.current_task is None

    def test_plan_open_and_search(self, automation):
        """Test planning an open and search task."""
        task = automation.plan_task("abre chrome y busca el clima")

        assert task is not None
        assert len(task.steps) > 0
        assert any("chrome" in s.description.lower() for s in task.steps)

    def test_plan_open_app(self, automation):
        """Test planning an open app task."""
        task = automation.plan_task("abre firefox")

        assert task is not None
        assert len(task.steps) >= 1

    def test_plan_generic_task(self, automation):
        """Test planning a generic task."""
        task = automation.plan_task("hacer algo complejo")

        assert task is not None
        assert len(task.steps) >= 1

    def test_get_plan_summary(self, automation):
        """Test getting plan summary."""
        automation.plan_task("abre chrome y busca noticias")

        summary = automation.get_plan_summary()

        assert "Plan para:" in summary
        assert "Pasos" in summary

    def test_get_plan_summary_no_task(self, automation):
        """Test summary when no task planned."""
        summary = automation.get_plan_summary()
        assert "No hay tarea" in summary

    def test_execute_wait_step(self, automation):
        """Test executing a wait step."""
        from modules.visual_automation import AutomationStep

        step = AutomationStep(
            description="Wait",
            action_type="wait",
            params={"seconds": 0.1}
        )

        result = automation._execute_step(step)
        assert "Esperado" in result

    def test_execute_open_app_step(self, automation):
        """Test executing an open app step."""
        from modules.visual_automation import AutomationStep

        step = AutomationStep(
            description="Open app",
            action_type="open_app",
            params={"app": "nonexistent_app_12345"}
        )

        result = automation._execute_step(step)
        # Should fail for nonexistent app
        assert "Error" in result or "Abierto" in result

    def test_execute_type_text_no_controller(self, automation):
        """Test typing without controller."""
        from modules.visual_automation import AutomationStep

        step = AutomationStep(
            description="Type",
            action_type="type_text",
            params={"text": "hello"}
        )

        result = automation._execute_step(step)
        assert "Error" in result or "Sin controlador" in result

    def test_confirm_without_task(self, automation):
        """Test confirming without a task."""
        result = automation.confirm_and_execute()
        assert "No hay tarea" in result


class TestVisualAutomationHandler:
    """Tests for VisualAutomationHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a VisualAutomationHandler instance."""
        from modules.visual_automation import VisualAutomationHandler

        handler = VisualAutomationHandler()
        yield handler
        handler.automation.reset()

    def test_initialization(self, handler):
        """Test handler initialization."""
        assert handler.automation is not None
        assert not handler.awaiting_confirmation

    def test_complex_task_query(self, handler):
        """Test complex task queries."""
        queries = [
            "abre chrome y busca el clima",
            "haz la tarea: abrir archivos",
        ]

        for query in queries:
            handler.awaiting_confirmation = False
            handler.automation.reset()

            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"
            assert "Plan para" in response or "Pasos" in response

    def test_confirmation_flow(self, handler):
        """Test confirmation flow."""
        # Plan a task
        handler.process_query("abre chrome y busca noticias")
        assert handler.awaiting_confirmation

        # Confirm
        is_handled, response = handler.process_query("sí")
        assert is_handled
        assert not handler.awaiting_confirmation

    def test_cancellation_flow(self, handler):
        """Test cancellation flow."""
        # Plan a task
        handler.process_query("abre firefox y busca algo")
        assert handler.awaiting_confirmation

        # Cancel
        is_handled, response = handler.process_query("no")
        assert is_handled
        assert "cancelada" in response.lower()
        assert not handler.awaiting_confirmation

    def test_non_automation_query(self, handler):
        """Test non-automation queries pass through."""
        queries = [
            "qué hora es",
            "cuánta memoria hay",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert not is_handled, f"Should NOT handle: {query}"


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_visual_automation(self):
        """Test get_visual_automation returns instance."""
        from modules import visual_automation

        # Reset singleton
        visual_automation._automation_instance = None

        automation = visual_automation.get_visual_automation()
        assert automation is not None

    def test_get_automation_handler(self):
        """Test get_automation_handler returns instance."""
        from modules import visual_automation

        # Reset singletons
        visual_automation._automation_instance = None
        visual_automation._handler_instance = None

        handler = visual_automation.get_automation_handler()
        assert handler is not None
