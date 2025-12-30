"""
JARVIS Memory Handler Module
Processes memory-related commands and manages conversational memory.
"""

import re
import logging
from typing import Optional, Tuple, List
from .database import MemoryDatabase, get_memory

logger = logging.getLogger(__name__)


class MemoryHandler:
    """Handles memory-related commands and context management."""

    # Patterns for detecting memory commands
    REMEMBER_PATTERNS = [
        r"recuerda\s+que\s+(.+)",
        r"recuerda:\s*(.+)",
        r"anota\s+que\s+(.+)",
        r"guarda\s+que\s+(.+)",
        r"no\s+olvides\s+que\s+(.+)",
        r"ten\s+en\s+cuenta\s+que\s+(.+)",
    ]

    FORGET_PATTERNS = [
        r"olvida\s+(?:lo\s+de\s+)?(.+)",
        r"borra\s+(?:lo\s+de\s+)?(.+)",
        r"elimina\s+(?:el\s+)?recuerdo\s+(?:de\s+)?(.+)",
    ]

    RECALL_PATTERNS = [
        r"qu[eé]\s+(?:recuerdas|sabes)\s+(?:sobre|de|acerca\s+de)\s+(.+)",
        r"qu[eé]\s+te\s+dije\s+(?:sobre|de)\s+(.+)",
        r"cu[aá]l\s+(?:es|era)\s+(.+)",
        r"recuerdas\s+(.+)",
    ]

    NAME_PATTERNS = [
        r"(?:me\s+llamo|mi\s+nombre\s+es|soy)\s+(\w+)",
        r"ll[aá]mame\s+(\w+)",
        r"puedes\s+llamarme\s+(\w+)",
    ]

    def __init__(self, db: Optional[MemoryDatabase] = None):
        self.db = db or get_memory()
        self.current_session_id: Optional[str] = None

    def start_session(self) -> str:
        """Start a new conversation session."""
        self.current_session_id = self.db.start_session()
        return self.current_session_id

    def end_session(self) -> None:
        """End the current conversation session."""
        if self.current_session_id:
            self.db.end_session(self.current_session_id)
            self.current_session_id = None

    def add_to_history(self, role: str, content: str) -> None:
        """Add a message to conversation history."""
        if self.current_session_id:
            self.db.add_conversation(self.current_session_id, role, content)

    def process_input(self, user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Process user input for memory commands.

        Returns:
            Tuple of (was_memory_command, response_if_handled)
            If it's a memory command, returns (True, response)
            If not, returns (False, None) so normal processing continues
        """
        user_input_lower = user_input.lower().strip()

        # Check for name setting
        name_response = self._check_name_setting(user_input_lower, user_input)
        if name_response:
            return (True, name_response)

        # Check for remember commands
        remember_response = self._check_remember_command(user_input_lower, user_input)
        if remember_response:
            return (True, remember_response)

        # Check for forget commands
        forget_response = self._check_forget_command(user_input_lower)
        if forget_response:
            return (True, forget_response)

        # Check for recall commands
        recall_response = self._check_recall_command(user_input_lower)
        if recall_response:
            return (True, recall_response)

        # Check for memory status queries
        if self._is_memory_status_query(user_input_lower):
            return (True, self._get_memory_status())

        return (False, None)

    def _check_name_setting(
        self,
        input_lower: str,
        original_input: str
    ) -> Optional[str]:
        """Check if user is introducing themselves."""
        for pattern in self.NAME_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                name = match.group(1).capitalize()
                self.db.set_user_name(name)
                self.db.add_memory(
                    f"El nombre del usuario es {name}",
                    category="personal",
                    keywords=["nombre", "usuario", "identidad"]
                )
                logger.info(f"User name learned: {name}")
                return f"Entendido, {name}. Me aseguraré de recordarlo."
        return None

    def _check_remember_command(
        self,
        input_lower: str,
        original_input: str
    ) -> Optional[str]:
        """Check if user is asking to remember something."""
        for pattern in self.REMEMBER_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                # Use original input to preserve case
                content_start = match.start(1)
                content = original_input[content_start:].strip()

                # Detect category from content
                category = self._detect_category(content)

                # Extract keywords
                keywords = self._extract_keywords(content)

                self.db.add_memory(content, category=category, keywords=keywords)
                logger.info(f"Memory stored: {content[:50]}...")

                responses = [
                    "Entendido, lo recordaré.",
                    "Anotado.",
                    "Lo tendré presente.",
                    "Guardado en memoria.",
                ]
                import random
                return random.choice(responses)
        return None

    def _check_forget_command(self, input_lower: str) -> Optional[str]:
        """Check if user is asking to forget something."""
        for pattern in self.FORGET_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                topic = match.group(1).strip()
                count = self.db.forget_about(topic)
                if count > 0:
                    return f"He olvidado {count} registro{'s' if count > 1 else ''} relacionado{'s' if count > 1 else ''} con {topic}."
                else:
                    return f"No tengo registros sobre {topic} que olvidar."
        return None

    def _check_recall_command(self, input_lower: str) -> Optional[str]:
        """Check if user is asking to recall something."""
        for pattern in self.RECALL_PATTERNS:
            match = re.search(pattern, input_lower)
            if match:
                topic = match.group(1).strip()
                topic = topic.rstrip("?").strip()
                memories = self.db.search_memories(topic, limit=5)
                if memories:
                    if len(memories) == 1:
                        return f"Recuerdo que: {memories[0]['content']}"
                    else:
                        lines = ["Esto es lo que recuerdo:"]
                        for mem in memories[:3]:
                            lines.append(f"- {mem['content']}")
                        return "\n".join(lines)
                else:
                    return f"No tengo recuerdos específicos sobre {topic}."
        return None

    def _is_memory_status_query(self, input_lower: str) -> bool:
        """Check if user is asking about memory status."""
        status_patterns = [
            r"qu[eé]\s+recuerdas",
            r"qu[eé]\s+sabes\s+(?:de|sobre)\s+m[ií]",
            r"cu[aá]nto\s+recuerdas",
            r"lista\s+(?:de\s+)?recuerdos",
            r"muestra\s+(?:tus\s+)?recuerdos",
        ]
        return any(re.search(p, input_lower) for p in status_patterns)

    def _get_memory_status(self) -> str:
        """Get a status report of stored memories."""
        summary = self.db.get_memory_summary()
        user_name = self.db.get_user_name()

        lines = []

        if user_name:
            lines.append(f"Su nombre es {user_name}.")

        if summary["memories"] > 0:
            lines.append(f"Tengo {summary['memories']} recuerdos almacenados.")
            recent = self.db.search_memories(limit=3)
            if recent:
                lines.append("Los más recientes:")
                for mem in recent:
                    lines.append(f"- {mem['content'][:60]}{'...' if len(mem['content']) > 60 else ''}")
        else:
            lines.append("No tengo recuerdos almacenados aún.")

        lines.append(f"Hemos tenido {summary['sessions']} sesiones de conversación.")

        return "\n".join(lines)

    def _detect_category(self, content: str) -> str:
        """Detect category from content keywords."""
        content_lower = content.lower()

        categories = {
            "personal": ["nombre", "cumpleaños", "familia", "esposa", "hijo", "hija"],
            "trabajo": ["cliente", "proyecto", "reunión", "trabajo", "empresa", "jefe"],
            "preferencias": ["me gusta", "prefiero", "favorito", "odio", "no me gusta"],
            "contactos": ["teléfono", "email", "correo", "dirección", "número"],
            "fechas": ["fecha", "aniversario", "día", "cumple"],
        }

        for category, keywords in categories.items():
            if any(kw in content_lower for kw in keywords):
                return category

        return "general"

    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content for indexing."""
        # Remove common words
        stopwords = {
            "el", "la", "los", "las", "un", "una", "unos", "unas",
            "de", "del", "al", "a", "en", "con", "por", "para",
            "que", "es", "son", "está", "están", "mi", "mis", "su", "sus",
            "y", "o", "pero", "como", "más", "muy", "también"
        }

        # Extract words
        words = re.findall(r'\b\w{3,}\b', content.lower())

        # Filter and return unique keywords
        keywords = [w for w in words if w not in stopwords]
        return list(set(keywords))[:10]

    def get_context_for_prompt(self) -> str:
        """
        Get memory context to include in Claude prompts.
        Returns relevant memories and user info.
        """
        context_parts = []

        # User name
        user_name = self.db.get_user_name()
        if user_name:
            context_parts.append(f"El usuario se llama {user_name}.")

        # Recent relevant memories (most accessed)
        memories = self.db.search_memories(limit=5)
        if memories:
            context_parts.append("Información recordada sobre el usuario:")
            for mem in memories:
                context_parts.append(f"- {mem['content']}")

        # User preferences
        prefs = self.db.get_all_preferences()
        if prefs:
            relevant_prefs = {k: v for k, v in prefs.items()
                           if k not in ["user_name"]}
            if relevant_prefs:
                context_parts.append("Preferencias del usuario:")
                for k, v in relevant_prefs.items():
                    context_parts.append(f"- {k}: {v}")

        return "\n".join(context_parts) if context_parts else ""

    def get_conversation_context(self, limit: int = 5) -> str:
        """Get recent conversation history as context."""
        return self.db.get_context_from_history(limit=limit)


# Singleton instance
_handler_instance: Optional[MemoryHandler] = None


def get_memory_handler() -> MemoryHandler:
    """Get or create the memory handler instance."""
    global _handler_instance

    if _handler_instance is None:
        _handler_instance = MemoryHandler()

    return _handler_instance
