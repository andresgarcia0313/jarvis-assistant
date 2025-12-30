"""
JARVIS Memory Database Module
Persistent storage using SQLite for memories, preferences, and conversation history.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class MemoryDatabase:
    """SQLite-based persistent memory for JARVIS."""

    def __init__(self, db_path: str = "memory/jarvis_memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"Memory database initialized at {self.db_path}")

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()

    def _init_database(self):
        """Initialize database tables."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Explicit memories table (things user asks JARVIS to remember)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT DEFAULT 'general',
                    content TEXT NOT NULL,
                    keywords TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP,
                    access_count INTEGER DEFAULT 0
                )
            """)

            # Conversation history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Session metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    message_count INTEGER DEFAULT 0
                )
            """)

            # Create indexes for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_category
                ON memories(category)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_memories_keywords
                ON memories(keywords)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_session
                ON conversations(session_id)
            """)

    # ==================== Preferences ====================

    def set_preference(self, key: str, value: Any) -> None:
        """Set a user preference."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            json_value = json.dumps(value) if not isinstance(value, str) else value
            cursor.execute("""
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, json_value, datetime.now()))
        logger.debug(f"Preference set: {key}")

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a user preference."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except json.JSONDecodeError:
                    return row["value"]
            return default

    def get_all_preferences(self) -> Dict[str, Any]:
        """Get all user preferences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM preferences")
            result = {}
            for row in cursor.fetchall():
                try:
                    result[row["key"]] = json.loads(row["value"])
                except json.JSONDecodeError:
                    result[row["key"]] = row["value"]
            return result

    def delete_preference(self, key: str) -> bool:
        """Delete a user preference."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM preferences WHERE key = ?", (key,))
            return cursor.rowcount > 0

    # ==================== Explicit Memories ====================

    def add_memory(
        self,
        content: str,
        category: str = "general",
        keywords: Optional[List[str]] = None
    ) -> int:
        """Add an explicit memory (something the user asks to remember)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            keywords_str = ",".join(keywords) if keywords else ""
            cursor.execute("""
                INSERT INTO memories (category, content, keywords, created_at)
                VALUES (?, ?, ?, ?)
            """, (category, content, keywords_str, datetime.now()))
            memory_id = cursor.lastrowid
        logger.info(f"Memory added: {content[:50]}...")
        return memory_id

    def search_memories(
        self,
        query: str = "",
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by content or keywords."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            conditions = []
            params = []

            if query:
                conditions.append("(content LIKE ? OR keywords LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            if category:
                conditions.append("category = ?")
                params.append(category)

            where_clause = " AND ".join(conditions) if conditions else "1=1"
            params.append(limit)

            cursor.execute(f"""
                SELECT id, category, content, keywords, created_at,
                       last_accessed, access_count
                FROM memories
                WHERE {where_clause}
                ORDER BY access_count DESC, created_at DESC
                LIMIT ?
            """, params)

            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "category": row["category"],
                    "content": row["content"],
                    "keywords": row["keywords"].split(",") if row["keywords"] else [],
                    "created_at": row["created_at"],
                    "last_accessed": row["last_accessed"],
                    "access_count": row["access_count"]
                })

            # Update access count for returned memories
            if results:
                memory_ids = [r["id"] for r in results]
                placeholders = ",".join("?" * len(memory_ids))
                cursor.execute(f"""
                    UPDATE memories
                    SET access_count = access_count + 1,
                        last_accessed = ?
                    WHERE id IN ({placeholders})
                """, [datetime.now()] + memory_ids)

            return results

    def get_all_memories(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all memories, optionally filtered by category."""
        return self.search_memories(category=category, limit=1000)

    def delete_memory(self, memory_id: int) -> bool:
        """Delete a specific memory."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    def forget_about(self, topic: str) -> int:
        """Delete all memories containing a specific topic."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM memories
                WHERE content LIKE ? OR keywords LIKE ?
            """, (f"%{topic}%", f"%{topic}%"))
            count = cursor.rowcount
        logger.info(f"Forgot {count} memories about: {topic}")
        return count

    # ==================== Conversation History ====================

    def start_session(self) -> str:
        """Start a new conversation session."""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (session_id, started_at)
                VALUES (?, ?)
            """, (session_id, datetime.now()))
        logger.info(f"Session started: {session_id}")
        return session_id

    def end_session(self, session_id: str) -> None:
        """End a conversation session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions
                SET ended_at = ?
                WHERE session_id = ?
            """, (datetime.now(), session_id))
        logger.info(f"Session ended: {session_id}")

    def add_conversation(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """Add a message to conversation history."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO conversations (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, datetime.now()))

            # Update session message count
            cursor.execute("""
                UPDATE sessions
                SET message_count = message_count + 1
                WHERE session_id = ?
            """, (session_id,))

    def get_conversation_history(
        self,
        session_id: str,
        limit: int = 20
    ) -> List[Dict[str, str]]:
        """Get conversation history for a session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT role, content, timestamp
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, limit))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["timestamp"]
                })
            return list(reversed(results))

    def get_recent_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get recent conversation sessions."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT session_id, started_at, ended_at, message_count
                FROM sessions
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,))

            results = []
            for row in cursor.fetchall():
                results.append({
                    "session_id": row["session_id"],
                    "started_at": row["started_at"],
                    "ended_at": row["ended_at"],
                    "message_count": row["message_count"]
                })
            return results

    def get_context_from_history(self, limit: int = 5) -> str:
        """Get recent conversation context as formatted string."""
        sessions = self.get_recent_sessions(limit=1)
        if not sessions:
            return ""

        history = self.get_conversation_history(
            sessions[0]["session_id"],
            limit=limit
        )

        if not history:
            return ""

        lines = []
        for msg in history:
            role = "Usuario" if msg["role"] == "user" else "JARVIS"
            lines.append(f"{role}: {msg['content']}")

        return "\n".join(lines)

    # ==================== Utility Methods ====================

    def get_user_name(self) -> Optional[str]:
        """Get the stored user name."""
        return self.get_preference("user_name")

    def set_user_name(self, name: str) -> None:
        """Set the user name."""
        self.set_preference("user_name", name)
        logger.info(f"User name set to: {name}")

    def get_memory_summary(self) -> Dict[str, Any]:
        """Get a summary of stored memories and preferences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) as count FROM memories")
            memory_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM preferences")
            pref_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM sessions")
            session_count = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM conversations")
            message_count = cursor.fetchone()["count"]

            return {
                "memories": memory_count,
                "preferences": pref_count,
                "sessions": session_count,
                "total_messages": message_count
            }

    def export_memories(self) -> Dict[str, Any]:
        """Export all data for backup."""
        return {
            "preferences": self.get_all_preferences(),
            "memories": self.get_all_memories(),
            "sessions": self.get_recent_sessions(limit=100),
            "exported_at": datetime.now().isoformat()
        }

    def clear_all(self) -> None:
        """Clear all stored data. Use with caution."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM preferences")
            cursor.execute("DELETE FROM memories")
            cursor.execute("DELETE FROM conversations")
            cursor.execute("DELETE FROM sessions")
        logger.warning("All memory data cleared")


# Singleton instance
_memory_instance: Optional[MemoryDatabase] = None


def get_memory(db_path: str = "memory/jarvis_memory.db") -> MemoryDatabase:
    """Get or create the memory database instance."""
    global _memory_instance

    if _memory_instance is None:
        _memory_instance = MemoryDatabase(db_path)

    return _memory_instance
