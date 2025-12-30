"""
JARVIS Reminders Module
Handles time-based reminders, work session alerts, and voice notes.
"""

import logging
import threading
import time
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Callable, Tuple
from dataclasses import dataclass, field, asdict
import sqlite3
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@dataclass
class Reminder:
    """A reminder entry."""
    id: Optional[int]
    message: str
    trigger_time: datetime
    created_at: datetime = field(default_factory=datetime.now)
    triggered: bool = False
    recurring: bool = False
    recurrence_minutes: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message": self.message,
            "trigger_time": self.trigger_time.isoformat(),
            "created_at": self.created_at.isoformat(),
            "triggered": self.triggered,
            "recurring": self.recurring,
            "recurrence_minutes": self.recurrence_minutes
        }


@dataclass
class WorkSession:
    """Tracks work session for break reminders."""
    started_at: datetime
    last_break_reminder: Optional[datetime] = None
    break_interval_minutes: int = 60


class ReminderDatabase:
    """SQLite storage for reminders."""

    def __init__(self, db_path: str = "memory/reminders.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_database(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    trigger_time TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    triggered BOOLEAN DEFAULT FALSE,
                    recurring BOOLEAN DEFAULT FALSE,
                    recurrence_minutes INTEGER DEFAULT 0
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_trigger_time
                ON reminders(trigger_time)
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS voice_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tags TEXT
                )
            """)

    def add_reminder(self, reminder: Reminder) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reminders
                (message, trigger_time, created_at, triggered, recurring, recurrence_minutes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                reminder.message,
                reminder.trigger_time.isoformat(),
                reminder.created_at.isoformat(),
                reminder.triggered,
                reminder.recurring,
                reminder.recurrence_minutes
            ))
            return cursor.lastrowid

    def get_pending_reminders(self) -> List[Reminder]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders
                WHERE triggered = FALSE
                ORDER BY trigger_time ASC
            """)
            return [self._row_to_reminder(row) for row in cursor.fetchall()]

    def get_due_reminders(self) -> List[Reminder]:
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reminders
                WHERE triggered = FALSE AND trigger_time <= ?
                ORDER BY trigger_time ASC
            """, (now,))
            return [self._row_to_reminder(row) for row in cursor.fetchall()]

    def mark_triggered(self, reminder_id: int) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE reminders SET triggered = TRUE WHERE id = ?
            """, (reminder_id,))

    def reschedule_recurring(self, reminder: Reminder) -> Optional[int]:
        if not reminder.recurring or reminder.recurrence_minutes <= 0:
            return None

        new_trigger = datetime.now() + timedelta(minutes=reminder.recurrence_minutes)
        new_reminder = Reminder(
            id=None,
            message=reminder.message,
            trigger_time=new_trigger,
            recurring=True,
            recurrence_minutes=reminder.recurrence_minutes
        )
        return self.add_reminder(new_reminder)

    def delete_reminder(self, reminder_id: int) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
            return cursor.rowcount > 0

    def clear_old_reminders(self, days: int = 7) -> int:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM reminders WHERE triggered = TRUE AND trigger_time < ?
            """, (cutoff,))
            return cursor.rowcount

    def _row_to_reminder(self, row) -> Reminder:
        return Reminder(
            id=row["id"],
            message=row["message"],
            trigger_time=datetime.fromisoformat(row["trigger_time"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            triggered=bool(row["triggered"]),
            recurring=bool(row["recurring"]),
            recurrence_minutes=row["recurrence_minutes"]
        )

    # Voice notes
    def add_voice_note(self, content: str, tags: List[str] = None) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            tags_str = ",".join(tags) if tags else ""
            cursor.execute("""
                INSERT INTO voice_notes (content, tags)
                VALUES (?, ?)
            """, (content, tags_str))
            return cursor.lastrowid

    def get_voice_notes(self, limit: int = 10) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM voice_notes
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [{
                "id": row["id"],
                "content": row["content"],
                "created_at": row["created_at"],
                "tags": row["tags"].split(",") if row["tags"] else []
            } for row in cursor.fetchall()]

    def search_voice_notes(self, query: str) -> List[Dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM voice_notes
                WHERE content LIKE ? OR tags LIKE ?
                ORDER BY created_at DESC
            """, (f"%{query}%", f"%{query}%"))
            return [{
                "id": row["id"],
                "content": row["content"],
                "created_at": row["created_at"],
                "tags": row["tags"].split(",") if row["tags"] else []
            } for row in cursor.fetchall()]


class ReminderManager:
    """Manages reminders and work session tracking."""

    # Time parsing patterns (Spanish)
    TIME_PATTERNS = [
        # "en X minutos/horas"
        (r"en\s+(\d+)\s*minutos?", "minutes"),
        (r"en\s+(\d+)\s*horas?", "hours"),
        (r"en\s+media\s+hora", "30min"),
        (r"en\s+una\s+hora", "1hour"),
        (r"en\s+un\s+cuarto\s+de\s+hora", "15min"),
        # "a las HH:MM"
        (r"a\s+las?\s+(\d{1,2})(?::(\d{2}))?", "at_time"),
        # "mañana a las HH:MM"
        (r"mañana\s+a\s+las?\s+(\d{1,2})(?::(\d{2}))?", "tomorrow_at"),
    ]

    REMINDER_PATTERNS = [
        r"recuérdame\s+(?:en\s+.+?\s+)?(?:que\s+)?(.+)",
        r"recuérdame\s+(.+)",
        r"pon\s+(?:un\s+)?recordatorio\s+(?:para\s+)?(.+)",
        r"avísame\s+(?:en\s+.+?\s+)?(?:cuando|que|para)\s+(.+)",
    ]

    NOTE_PATTERNS = [
        r"anota(?:\s+que)?\s+(.+)",
        r"toma\s+nota(?:\s+de)?(?:\s+que)?\s+(.+)",
        r"guarda\s+(?:esta\s+)?nota(?:\s+que)?\s*:?\s*(.+)",
        r"nota\s+de\s+voz(?:\s*:)?\s*(.+)",
    ]

    def __init__(
        self,
        db_path: str = "memory/reminders.db",
        on_reminder: Optional[Callable[[str], None]] = None,
        check_interval: float = 30.0,
        work_break_interval: int = 60
    ):
        self.db = ReminderDatabase(db_path)
        self.on_reminder = on_reminder
        self.check_interval = check_interval
        self.work_break_interval = work_break_interval

        self._running = False
        self._check_thread: Optional[threading.Thread] = None
        self._work_session: Optional[WorkSession] = None

        logger.info("Reminder manager initialized")

    def start(self) -> None:
        """Start the reminder checking thread."""
        if self._running:
            return

        self._running = True
        self._work_session = WorkSession(
            started_at=datetime.now(),
            break_interval_minutes=self.work_break_interval
        )
        self._check_thread = threading.Thread(
            target=self._check_loop,
            daemon=True
        )
        self._check_thread.start()
        logger.info("Reminder manager started")

    def stop(self) -> None:
        """Stop the reminder checking thread."""
        self._running = False
        if self._check_thread:
            self._check_thread.join(timeout=2)
        logger.info("Reminder manager stopped")

    def _check_loop(self) -> None:
        """Background loop to check for due reminders."""
        while self._running:
            try:
                self._process_due_reminders()
                self._check_work_session()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in reminder check loop: {e}")

    def _process_due_reminders(self) -> None:
        """Process all due reminders."""
        due = self.db.get_due_reminders()
        for reminder in due:
            self._trigger_reminder(reminder)

    def _trigger_reminder(self, reminder: Reminder) -> None:
        """Trigger a reminder."""
        message = f"Señor, le recuerdo: {reminder.message}"
        logger.info(f"Triggering reminder: {reminder.message}")

        if self.on_reminder:
            self.on_reminder(message)

        self.db.mark_triggered(reminder.id)

        # Handle recurring reminders
        if reminder.recurring:
            self.db.reschedule_recurring(reminder)

    def _check_work_session(self) -> None:
        """Check if work break reminder is due."""
        if not self._work_session:
            return

        now = datetime.now()
        session_duration = (now - self._work_session.started_at).total_seconds() / 60

        # Check if break reminder is due
        last_reminder = self._work_session.last_break_reminder or self._work_session.started_at
        since_last = (now - last_reminder).total_seconds() / 60

        if since_last >= self._work_session.break_interval_minutes:
            hours = int(session_duration // 60)
            minutes = int(session_duration % 60)

            if hours > 0:
                duration_str = f"{hours} hora{'s' if hours > 1 else ''}"
                if minutes > 0:
                    duration_str += f" y {minutes} minutos"
            else:
                duration_str = f"{minutes} minutos"

            message = f"Señor, lleva {duration_str} trabajando. Quizás sea buen momento para un descanso."

            if self.on_reminder:
                self.on_reminder(message)

            self._work_session.last_break_reminder = now

    def reset_work_session(self) -> None:
        """Reset the work session timer."""
        self._work_session = WorkSession(
            started_at=datetime.now(),
            break_interval_minutes=self.work_break_interval
        )
        logger.info("Work session reset")

    def get_work_duration(self) -> Optional[timedelta]:
        """Get current work session duration."""
        if not self._work_session:
            return None
        return datetime.now() - self._work_session.started_at

    # ==================== Reminder Creation ====================

    def parse_and_create_reminder(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Parse user input and create a reminder if applicable.

        Returns:
            Tuple of (was_reminder_request, response_message)
        """
        input_lower = user_input.lower().strip()

        # Check if it's a reminder request
        reminder_content = None
        for pattern in self.REMINDER_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                reminder_content = match.group(1).strip()
                break

        if not reminder_content:
            return (False, None)

        # Parse time from the input
        trigger_time = self._parse_time(user_input)

        if not trigger_time:
            # Default to 30 minutes
            trigger_time = datetime.now() + timedelta(minutes=30)
            time_desc = "en 30 minutos"
        else:
            time_desc = self._format_time(trigger_time)

        # Clean up the reminder message
        message = self._clean_reminder_message(reminder_content)

        # Create the reminder
        reminder = Reminder(
            id=None,
            message=message,
            trigger_time=trigger_time
        )
        reminder_id = self.db.add_reminder(reminder)

        response = f"Entendido. Le recordaré {time_desc}: {message}"
        logger.info(f"Created reminder #{reminder_id}: {message} at {trigger_time}")

        return (True, response)

    def _parse_time(self, text: str) -> Optional[datetime]:
        """Parse time reference from text."""
        text_lower = text.lower()

        for pattern, time_type in self.TIME_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                if time_type == "minutes":
                    minutes = int(match.group(1))
                    return datetime.now() + timedelta(minutes=minutes)

                elif time_type == "hours":
                    hours = int(match.group(1))
                    return datetime.now() + timedelta(hours=hours)

                elif time_type == "30min":
                    return datetime.now() + timedelta(minutes=30)

                elif time_type == "1hour":
                    return datetime.now() + timedelta(hours=1)

                elif time_type == "15min":
                    return datetime.now() + timedelta(minutes=15)

                elif time_type == "at_time":
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    target = datetime.now().replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    if target <= datetime.now():
                        target += timedelta(days=1)
                    return target

                elif time_type == "tomorrow_at":
                    hour = int(match.group(1))
                    minute = int(match.group(2)) if match.group(2) else 0
                    target = datetime.now().replace(
                        hour=hour, minute=minute, second=0, microsecond=0
                    )
                    target += timedelta(days=1)
                    return target

        return None

    def _clean_reminder_message(self, message: str) -> str:
        """Clean time references from reminder message."""
        # Remove time patterns from the message
        patterns_to_remove = [
            r"en\s+\d+\s*minutos?\s*",
            r"en\s+\d+\s*horas?\s*",
            r"en\s+media\s+hora\s*",
            r"en\s+una\s+hora\s*",
            r"a\s+las?\s+\d{1,2}(?::\d{2})?\s*",
            r"mañana\s+",
        ]

        result = message
        for pattern in patterns_to_remove:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)

        return result.strip()

    def _format_time(self, dt: datetime) -> str:
        """Format datetime for speech."""
        now = datetime.now()
        diff = dt - now

        if diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"en {minutes} minuto{'s' if minutes != 1 else ''}"
        elif diff.total_seconds() < 86400:
            if dt.date() == now.date():
                return f"hoy a las {dt.strftime('%H:%M')}"
            else:
                return f"mañana a las {dt.strftime('%H:%M')}"
        else:
            return f"el {dt.strftime('%d/%m a las %H:%M')}"

    # ==================== Voice Notes ====================

    def parse_and_create_note(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Parse user input and create a voice note if applicable."""
        input_lower = user_input.lower().strip()

        note_content = None
        for pattern in self.NOTE_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                # Get original case content
                start = match.start(1)
                note_content = user_input[start:].strip()
                break

        if not note_content:
            return (False, None)

        # Extract tags (words starting with #)
        tags = re.findall(r'#(\w+)', note_content)

        # Store the note
        self.db.add_voice_note(note_content, tags)

        response = "Nota guardada."
        logger.info(f"Voice note saved: {note_content[:50]}...")

        return (True, response)

    # ==================== Queries ====================

    def get_pending_reminders_summary(self) -> str:
        """Get summary of pending reminders."""
        pending = self.db.get_pending_reminders()

        if not pending:
            return "No tiene recordatorios pendientes."

        lines = [f"Tiene {len(pending)} recordatorio{'s' if len(pending) > 1 else ''} pendiente{'s' if len(pending) > 1 else ''}:"]

        for reminder in pending[:5]:
            time_str = self._format_time(reminder.trigger_time)
            lines.append(f"- {time_str}: {reminder.message}")

        if len(pending) > 5:
            lines.append(f"... y {len(pending) - 5} más.")

        return "\n".join(lines)

    def cancel_reminder(self, query: str) -> str:
        """Cancel a reminder matching the query."""
        pending = self.db.get_pending_reminders()

        for reminder in pending:
            if query.lower() in reminder.message.lower():
                self.db.delete_reminder(reminder.id)
                return f"Recordatorio cancelado: {reminder.message}"

        return "No encontré un recordatorio que coincida."


class ReminderQueryHandler:
    """Handles reminder-related queries from user input."""

    QUERY_PATTERNS = [
        (r"qu[eé]\s+recordatorios\s+tengo", "list"),
        (r"mis\s+recordatorios", "list"),
        (r"recordatorios\s+pendientes", "list"),
        (r"cancela\s+(?:el\s+)?recordatorio\s+(?:de\s+)?(.+)", "cancel"),
        (r"borra\s+(?:el\s+)?recordatorio\s+(?:de\s+)?(.+)", "cancel"),
        (r"cu[aá]nto\s+(?:tiempo\s+)?llevo\s+trabajando", "work_time"),
        (r"cu[aá]nto\s+llevo\s+en\s+(?:la\s+)?sesi[oó]n", "work_time"),
        (r"reinicia\s+(?:el\s+)?(?:contador|timer|sesi[oó]n)", "reset_session"),
        (r"mis\s+notas", "notes"),
        (r"qu[eé]\s+notas\s+tengo", "notes"),
    ]

    def __init__(self, manager: Optional[ReminderManager] = None):
        self.manager = manager or ReminderManager()

    def process_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """Process user input for reminder commands."""
        input_lower = user_input.lower().strip()

        # Check for queries
        for pattern, query_type in self.QUERY_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                return (True, self._handle_query(query_type, match))

        # Check for reminder creation
        is_reminder, response = self.manager.parse_and_create_reminder(user_input)
        if is_reminder:
            return (True, response)

        # Check for voice note creation
        is_note, response = self.manager.parse_and_create_note(user_input)
        if is_note:
            return (True, response)

        return (False, None)

    def _handle_query(self, query_type: str, match) -> str:
        if query_type == "list":
            return self.manager.get_pending_reminders_summary()

        elif query_type == "cancel":
            query = match.group(1).strip()
            return self.manager.cancel_reminder(query)

        elif query_type == "work_time":
            duration = self.manager.get_work_duration()
            if duration:
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                if hours > 0:
                    return f"Lleva {hours} hora{'s' if hours > 1 else ''} y {minutes} minutos en esta sesión."
                else:
                    return f"Lleva {minutes} minutos en esta sesión."
            return "No hay una sesión de trabajo activa."

        elif query_type == "reset_session":
            self.manager.reset_work_session()
            return "Sesión de trabajo reiniciada."

        elif query_type == "notes":
            notes = self.manager.db.get_voice_notes(limit=5)
            if not notes:
                return "No tiene notas guardadas."
            lines = ["Sus notas recientes:"]
            for note in notes:
                content = note["content"][:50]
                if len(note["content"]) > 50:
                    content += "..."
                lines.append(f"- {content}")
            return "\n".join(lines)

        return "No entendí la consulta."


# Singleton instances
_manager_instance: Optional[ReminderManager] = None
_handler_instance: Optional[ReminderQueryHandler] = None


def get_reminder_manager(
    on_reminder: Optional[Callable[[str], None]] = None
) -> ReminderManager:
    """Get or create the reminder manager instance."""
    global _manager_instance

    if _manager_instance is None:
        _manager_instance = ReminderManager(on_reminder=on_reminder)

    return _manager_instance


def get_reminder_handler() -> ReminderQueryHandler:
    """Get or create the reminder query handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = ReminderQueryHandler(get_reminder_manager())

    return _handler_instance
