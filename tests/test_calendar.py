"""
Tests for JARVIS Calendar Integration module.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestCalendarEvent:
    """Tests for CalendarEvent dataclass."""

    def test_event_creation(self):
        """Test creating a calendar event."""
        from modules.calendar_integration import CalendarEvent

        event = CalendarEvent(
            uid="test-123",
            summary="Team Meeting",
            start=datetime.now(),
            end=datetime.now() + timedelta(hours=1),
            location="Room 101"
        )

        assert event.uid == "test-123"
        assert event.summary == "Team Meeting"
        assert event.location == "Room 101"

    def test_duration_minutes(self):
        """Test calculating event duration."""
        from modules.calendar_integration import CalendarEvent

        start = datetime.now()
        end = start + timedelta(hours=1, minutes=30)

        event = CalendarEvent(
            uid="test",
            summary="Test",
            start=start,
            end=end
        )

        assert event.duration_minutes() == 90

    def test_is_happening_now(self):
        """Test checking if event is happening now."""
        from modules.calendar_integration import CalendarEvent

        # Event happening now
        now_event = CalendarEvent(
            uid="now",
            summary="Now",
            start=datetime.now() - timedelta(minutes=30),
            end=datetime.now() + timedelta(minutes=30)
        )
        assert now_event.is_happening_now()

        # Past event
        past_event = CalendarEvent(
            uid="past",
            summary="Past",
            start=datetime.now() - timedelta(hours=2),
            end=datetime.now() - timedelta(hours=1)
        )
        assert not past_event.is_happening_now()

    def test_starts_in_minutes(self):
        """Test calculating minutes until event starts."""
        from modules.calendar_integration import CalendarEvent

        event = CalendarEvent(
            uid="future",
            summary="Future",
            start=datetime.now() + timedelta(minutes=30),
            end=datetime.now() + timedelta(minutes=90)
        )

        minutes = event.starts_in_minutes()
        assert 29 <= minutes <= 31


class TestCalendarManager:
    """Tests for CalendarManager class."""

    @pytest.fixture
    def manager(self):
        """Create a calendar manager."""
        from modules.calendar_integration import CalendarManager
        mgr = CalendarManager(ics_paths=[])
        yield mgr
        mgr.stop_monitoring()

    def test_initialization(self, manager):
        """Test manager initialization."""
        assert manager.events == []

    def test_get_todays_events_empty(self, manager):
        """Test getting today's events when empty."""
        events = manager.get_todays_events()
        assert events == []

    def test_get_todays_events(self, manager):
        """Test getting today's events."""
        from modules.calendar_integration import CalendarEvent

        now = datetime.now()

        # Add today's event
        manager.events.append(CalendarEvent(
            uid="today",
            summary="Today's meeting",
            start=now.replace(hour=14, minute=0),
            end=now.replace(hour=15, minute=0)
        ))

        # Add tomorrow's event
        tomorrow = now + timedelta(days=1)
        manager.events.append(CalendarEvent(
            uid="tomorrow",
            summary="Tomorrow's meeting",
            start=tomorrow.replace(hour=10, minute=0),
            end=tomorrow.replace(hour=11, minute=0)
        ))

        today_events = manager.get_todays_events()
        assert len(today_events) == 1
        assert today_events[0].summary == "Today's meeting"

    def test_get_upcoming_events(self, manager):
        """Test getting upcoming events."""
        from modules.calendar_integration import CalendarEvent

        now = datetime.now()

        # Add upcoming event
        manager.events.append(CalendarEvent(
            uid="upcoming",
            summary="Upcoming",
            start=now + timedelta(hours=2),
            end=now + timedelta(hours=3)
        ))

        # Add far future event
        manager.events.append(CalendarEvent(
            uid="far",
            summary="Far future",
            start=now + timedelta(days=7),
            end=now + timedelta(days=7, hours=1)
        ))

        upcoming = manager.get_upcoming_events(hours=24)
        assert len(upcoming) == 1
        assert upcoming[0].summary == "Upcoming"

    def test_get_next_event(self, manager):
        """Test getting next event."""
        from modules.calendar_integration import CalendarEvent

        now = datetime.now()

        manager.events.append(CalendarEvent(
            uid="next",
            summary="Next meeting",
            start=now + timedelta(hours=1),
            end=now + timedelta(hours=2)
        ))

        next_event = manager.get_next_event()
        assert next_event is not None
        assert next_event.summary == "Next meeting"

    def test_get_events_summary_empty(self, manager):
        """Test events summary when empty."""
        summary = manager.get_events_summary()
        assert "no tiene" in summary.lower() or "no hay" in summary.lower()

    def test_get_events_summary(self, manager):
        """Test events summary with events."""
        from modules.calendar_integration import CalendarEvent

        now = datetime.now()

        manager.events.append(CalendarEvent(
            uid="meeting1",
            summary="Meeting 1",
            start=now.replace(hour=10, minute=0),
            end=now.replace(hour=11, minute=0)
        ))

        summary = manager.get_events_summary()
        assert "Meeting 1" in summary or "1 evento" in summary

    def test_get_next_meeting_info_empty(self, manager):
        """Test next meeting info when empty."""
        info = manager.get_next_meeting_info()
        assert "no tiene" in info.lower()

    def test_get_next_meeting_info(self, manager):
        """Test next meeting info."""
        from modules.calendar_integration import CalendarEvent

        now = datetime.now()

        manager.events.append(CalendarEvent(
            uid="meeting",
            summary="Important Meeting",
            start=now + timedelta(minutes=30),
            end=now + timedelta(hours=1, minutes=30)
        ))

        info = manager.get_next_meeting_info()
        assert "Important Meeting" in info

    def test_reminder_callback(self, manager):
        """Test meeting reminder callback."""
        from modules.calendar_integration import CalendarEvent

        reminders = []

        def on_reminder(msg):
            reminders.append(msg)

        manager.set_reminder_callback(on_reminder)

        now = datetime.now()

        # Add event starting in 5 minutes
        event = CalendarEvent(
            uid="soon",
            summary="Soon Meeting",
            start=now + timedelta(minutes=5),
            end=now + timedelta(hours=1)
        )
        manager.events.append(event)

        # Trigger check
        manager._check_upcoming_meetings()

        assert len(reminders) >= 1
        assert "Soon Meeting" in reminders[0]


class TestCalendarQueryHandler:
    """Tests for CalendarQueryHandler class."""

    @pytest.fixture
    def handler(self):
        """Create a calendar query handler."""
        from modules.calendar_integration import CalendarManager, CalendarQueryHandler
        manager = CalendarManager(ics_paths=[])
        handler = CalendarQueryHandler(manager)
        yield handler

    def test_today_queries(self, handler):
        """Test today's events queries."""
        queries = [
            "qué tengo en el calendario hoy",
            "eventos de hoy",
            "qué reuniones tengo",
            "agenda de hoy",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"

    def test_next_meeting_queries(self, handler):
        """Test next meeting queries."""
        queries = [
            "próxima reunión",
            "siguiente reunión",
            "cuándo es la próxima reunión",
        ]

        for query in queries:
            is_handled, response = handler.process_query(query)
            assert is_handled, f"Should handle: {query}"

    def test_non_calendar_query(self, handler):
        """Test non-calendar queries pass through."""
        is_handled, response = handler.process_query("qué hora es")
        assert not is_handled


class TestICSParsing:
    """Tests for ICS file parsing."""

    @pytest.fixture
    def sample_ics(self):
        """Create a sample ICS file."""
        ics_content = """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test//EN
BEGIN:VEVENT
UID:test-event-123
DTSTART:20251230T100000
DTEND:20251230T110000
SUMMARY:Test Meeting
LOCATION:Conference Room A
DESCRIPTION:This is a test meeting
END:VEVENT
BEGIN:VEVENT
UID:test-event-456
DTSTART:20251230
DTEND:20251231
SUMMARY:All Day Event
END:VEVENT
END:VCALENDAR"""

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.ics', delete=False
        ) as f:
            f.write(ics_content)
            ics_path = f.name

        yield ics_path

        if os.path.exists(ics_path):
            os.unlink(ics_path)

    def test_load_ics_file(self, sample_ics):
        """Test loading events from ICS file."""
        from modules.calendar_integration import CalendarManager

        manager = CalendarManager(ics_paths=[sample_ics])
        manager.load_events()

        assert len(manager.events) == 2

    def test_parse_regular_event(self, sample_ics):
        """Test parsing a regular event."""
        from modules.calendar_integration import CalendarManager

        manager = CalendarManager(ics_paths=[sample_ics])
        manager.load_events()

        regular_events = [e for e in manager.events if not e.all_day]
        assert len(regular_events) >= 1

        event = regular_events[0]
        assert event.summary == "Test Meeting"
        assert event.location == "Conference Room A"
        assert not event.all_day

    def test_parse_all_day_event(self, sample_ics):
        """Test parsing an all-day event."""
        from modules.calendar_integration import CalendarManager

        manager = CalendarManager(ics_paths=[sample_ics])
        manager.load_events()

        all_day_events = [e for e in manager.events if e.all_day]
        assert len(all_day_events) >= 1

        event = all_day_events[0]
        assert event.summary == "All Day Event"
        assert event.all_day


class TestSingletons:
    """Tests for singleton functions."""

    def test_get_calendar_manager(self):
        """Test get_calendar_manager returns instance."""
        from modules import calendar_integration as cal

        # Reset singleton
        cal._calendar_instance = None

        manager = cal.get_calendar_manager()
        assert manager is not None

    def test_get_calendar_handler(self):
        """Test get_calendar_handler returns instance."""
        from modules import calendar_integration as cal

        # Reset singletons
        cal._calendar_instance = None
        cal._handler_instance = None

        handler = cal.get_calendar_handler()
        assert handler is not None
