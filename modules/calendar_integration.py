"""
JARVIS Calendar Integration Module
Supports local ICS files and provides meeting awareness.
"""

import logging
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
import threading
import time

logger = logging.getLogger(__name__)

# Try to import icalendar for ICS parsing
try:
    from icalendar import Calendar as ICalendar
    HAS_ICALENDAR = True
except ImportError:
    HAS_ICALENDAR = False
    logger.warning("icalendar not installed. ICS file support disabled.")


@dataclass
class CalendarEvent:
    """A calendar event."""
    uid: str
    summary: str
    start: datetime
    end: datetime
    location: Optional[str] = None
    description: Optional[str] = None
    all_day: bool = False

    def duration_minutes(self) -> int:
        return int((self.end - self.start).total_seconds() / 60)

    def is_happening_now(self) -> bool:
        now = datetime.now()
        return self.start <= now <= self.end

    def starts_in_minutes(self) -> int:
        now = datetime.now()
        if self.start <= now:
            return 0
        return int((self.start - now).total_seconds() / 60)


class CalendarManager:
    """Manages calendar events from ICS files."""

    def __init__(
        self,
        ics_paths: Optional[List[str]] = None,
        check_interval: float = 300.0,  # 5 minutes
        reminder_minutes: List[int] = None
    ):
        self.ics_paths = ics_paths or []
        self.check_interval = check_interval
        self.reminder_minutes = reminder_minutes or [15, 5]
        self.events: List[CalendarEvent] = []
        self._last_load: Optional[datetime] = None
        self._reminded_events: Dict[str, List[int]] = {}  # uid -> [minutes already reminded]
        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._on_meeting_reminder: Optional[callable] = None

        # Try common calendar locations
        if not self.ics_paths:
            self._discover_calendars()

        logger.info(f"Calendar manager initialized with {len(self.ics_paths)} calendar(s)")

    def _discover_calendars(self) -> None:
        """Discover common calendar file locations."""
        home = Path.home()
        common_paths = [
            home / ".local/share/evolution/calendar/system/calendar.ics",
            home / ".local/share/gnome-calendar/local.calendar/calendar.ics",
            home / ".local/share/korganizer/calendar.ics",
            home / ".thunderbird" / "*.default*" / "calendar-data" / "local.ics",
            home / "Calendars" / "*.ics",
            home / ".calendars" / "*.ics",
        ]

        for pattern in common_paths:
            pattern_str = str(pattern)
            if "*" in pattern_str:
                # Handle glob patterns
                parent = Path(pattern_str.split("*")[0])
                if parent.exists():
                    for f in parent.rglob("*.ics"):
                        if f.is_file():
                            self.ics_paths.append(str(f))
            else:
                path = Path(pattern_str)
                if path.exists():
                    self.ics_paths.append(str(path))

    def load_events(self) -> None:
        """Load events from all ICS files."""
        if not HAS_ICALENDAR:
            logger.warning("Cannot load ICS files: icalendar not installed")
            return

        self.events = []

        for ics_path in self.ics_paths:
            try:
                path = Path(ics_path)
                if not path.exists():
                    continue

                with open(path, 'rb') as f:
                    cal = ICalendar.from_ical(f.read())

                for component in cal.walk():
                    if component.name == "VEVENT":
                        event = self._parse_event(component)
                        if event:
                            self.events.append(event)

            except Exception as e:
                logger.error(f"Error loading calendar {ics_path}: {e}")

        self._last_load = datetime.now()
        logger.info(f"Loaded {len(self.events)} calendar events")

    def _parse_event(self, component) -> Optional[CalendarEvent]:
        """Parse an iCalendar event component."""
        try:
            uid = str(component.get('uid', ''))
            summary = str(component.get('summary', 'Sin título'))

            dtstart = component.get('dtstart')
            dtend = component.get('dtend')

            if not dtstart:
                return None

            start_dt = dtstart.dt
            all_day = False

            # Handle all-day events (date vs datetime)
            if not hasattr(start_dt, 'hour'):
                all_day = True
                start_dt = datetime.combine(start_dt, datetime.min.time())

            if dtend:
                end_dt = dtend.dt
                if not hasattr(end_dt, 'hour'):
                    end_dt = datetime.combine(end_dt, datetime.min.time())
            else:
                # Default duration: 1 hour or all day
                if all_day:
                    end_dt = start_dt + timedelta(days=1)
                else:
                    end_dt = start_dt + timedelta(hours=1)

            # Make timezone naive for comparison
            if hasattr(start_dt, 'tzinfo') and start_dt.tzinfo:
                start_dt = start_dt.replace(tzinfo=None)
            if hasattr(end_dt, 'tzinfo') and end_dt.tzinfo:
                end_dt = end_dt.replace(tzinfo=None)

            location = str(component.get('location', '')) or None
            description = str(component.get('description', '')) or None

            return CalendarEvent(
                uid=uid,
                summary=summary,
                start=start_dt,
                end=end_dt,
                location=location,
                description=description,
                all_day=all_day
            )

        except Exception as e:
            logger.debug(f"Error parsing event: {e}")
            return None

    def set_reminder_callback(self, callback: callable) -> None:
        """Set callback for meeting reminders."""
        self._on_meeting_reminder = callback

    def start_monitoring(self) -> None:
        """Start background monitoring for calendar events."""
        if self._running:
            return

        self._running = True
        self._check_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True
        )
        self._check_thread.start()
        logger.info("Calendar monitoring started")

    def stop_monitoring(self) -> None:
        """Stop calendar monitoring."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=2)
        logger.info("Calendar monitoring stopped")

    def _monitor_loop(self) -> None:
        """Background loop for calendar monitoring."""
        # Initial load
        self.load_events()

        while self._running:
            try:
                # Reload periodically
                if self._last_load and (datetime.now() - self._last_load).total_seconds() > 3600:
                    self.load_events()

                # Check for upcoming meetings
                self._check_upcoming_meetings()

                time.sleep(self.check_interval)

            except Exception as e:
                logger.error(f"Error in calendar monitor: {e}")

    def _check_upcoming_meetings(self) -> None:
        """Check for upcoming meetings and send reminders."""
        if not self._on_meeting_reminder:
            return

        now = datetime.now()
        today_end = now.replace(hour=23, minute=59, second=59)

        for event in self.events:
            if event.start < now or event.start > today_end:
                continue

            if event.all_day:
                continue

            minutes_until = event.starts_in_minutes()

            for reminder_minutes in self.reminder_minutes:
                # Check if we should remind at this interval
                if minutes_until <= reminder_minutes:
                    reminded = self._reminded_events.get(event.uid, [])
                    if reminder_minutes not in reminded:
                        self._send_meeting_reminder(event, minutes_until)
                        reminded.append(reminder_minutes)
                        self._reminded_events[event.uid] = reminded
                        break

    def _send_meeting_reminder(self, event: CalendarEvent, minutes: int) -> None:
        """Send a meeting reminder."""
        if minutes <= 0:
            message = f"Señor, su reunión '{event.summary}' está comenzando ahora."
        elif minutes == 1:
            message = f"Señor, su reunión '{event.summary}' comienza en 1 minuto."
        else:
            message = f"Señor, su reunión '{event.summary}' comienza en {minutes} minutos."

        if event.location:
            message += f" Ubicación: {event.location}."

        logger.info(f"Meeting reminder: {event.summary}")

        if self._on_meeting_reminder:
            self._on_meeting_reminder(message)

    # ==================== Queries ====================

    def get_todays_events(self) -> List[CalendarEvent]:
        """Get today's events."""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        return [
            e for e in self.events
            if today_start <= e.start < today_end
        ]

    def get_upcoming_events(self, hours: int = 24) -> List[CalendarEvent]:
        """Get upcoming events in the next N hours."""
        now = datetime.now()
        end = now + timedelta(hours=hours)

        return sorted([
            e for e in self.events
            if now <= e.start <= end
        ], key=lambda e: e.start)

    def get_next_event(self) -> Optional[CalendarEvent]:
        """Get the next upcoming event."""
        upcoming = self.get_upcoming_events(hours=72)
        return upcoming[0] if upcoming else None

    def get_events_summary(self) -> str:
        """Get a summary of today's events."""
        today_events = self.get_todays_events()

        if not today_events:
            return "No tiene eventos programados para hoy."

        # Sort by start time
        today_events = sorted(today_events, key=lambda e: e.start)

        lines = [f"Tiene {len(today_events)} evento{'s' if len(today_events) > 1 else ''} hoy:"]

        for event in today_events[:5]:
            if event.all_day:
                time_str = "Todo el día"
            else:
                time_str = event.start.strftime("%H:%M")
            lines.append(f"- {time_str}: {event.summary}")

        if len(today_events) > 5:
            lines.append(f"... y {len(today_events) - 5} más.")

        return "\n".join(lines)

    def get_next_meeting_info(self) -> str:
        """Get info about the next meeting."""
        upcoming = [e for e in self.get_upcoming_events(hours=24) if not e.all_day]

        if not upcoming:
            return "No tiene reuniones próximas en las siguientes 24 horas."

        event = upcoming[0]
        minutes = event.starts_in_minutes()

        if minutes <= 0:
            return f"Su reunión '{event.summary}' está en curso."
        elif minutes < 60:
            return f"Su próxima reunión es '{event.summary}' en {minutes} minutos."
        else:
            hours = minutes // 60
            mins = minutes % 60
            time_str = f"{hours} hora{'s' if hours > 1 else ''}"
            if mins > 0:
                time_str += f" y {mins} minutos"
            return f"Su próxima reunión es '{event.summary}' en {time_str}."


class CalendarQueryHandler:
    """Handles calendar-related queries."""

    PATTERNS = [
        (r"qu[eé]\s+(?:tengo|hay)\s+(?:en\s+)?(?:el\s+)?(?:calendario|agenda)\s*(?:hoy)?", "today"),
        (r"(?:mis\s+)?eventos?\s+(?:de\s+)?hoy", "today"),
        (r"qu[eé]\s+reuniones\s+tengo", "today"),
        (r"agenda\s+(?:de\s+)?hoy", "today"),
        (r"pr[oó]xima\s+reuni[oó]n", "next"),
        (r"siguiente\s+reuni[oó]n", "next"),
        (r"cu[aá]ndo\s+(?:es\s+)?(?:la\s+)?(?:pr[oó]xima|siguiente)\s+reuni[oó]n", "next"),
    ]

    def __init__(self, manager: Optional[CalendarManager] = None):
        self.manager = manager or CalendarManager()

    def process_query(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process a calendar-related query."""
        input_lower = user_input.lower().strip()

        for pattern, query_type in self.PATTERNS:
            if re.search(pattern, input_lower):
                response = self._handle_query(query_type)
                return (True, response)

        return (False, None)

    def _handle_query(self, query_type: str) -> str:
        if query_type == "today":
            return self.manager.get_events_summary()
        elif query_type == "next":
            return self.manager.get_next_meeting_info()
        return "No entendí la consulta del calendario."


# Singleton instances
_calendar_instance: Optional[CalendarManager] = None
_handler_instance: Optional[CalendarQueryHandler] = None


def get_calendar_manager() -> CalendarManager:
    """Get or create the calendar manager instance."""
    global _calendar_instance

    if _calendar_instance is None:
        _calendar_instance = CalendarManager()

    return _calendar_instance


def get_calendar_handler() -> CalendarQueryHandler:
    """Get or create the calendar query handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = CalendarQueryHandler(get_calendar_manager())

    return _handler_instance
