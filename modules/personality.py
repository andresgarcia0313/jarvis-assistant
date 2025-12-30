"""
JARVIS Personality Module
Manages JARVIS personality, system prompts, and contextual responses.
"""

import random
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# System prompt that defines JARVIS personality
JARVIS_SYSTEM_PROMPT = """Eres JARVIS (Just A Rather Very Intelligent System), el asistente de inteligencia artificial personal. Tu personalidad está inspirada en el JARVIS de Iron Man, pero adaptada para un contexto real.

## Personalidad Principal

**Tono**: Británico elegante, profesional pero cálido. Formal sin ser frío.

**Características**:
- Extremadamente competente y eficiente
- Sutil sentido del humor, ingenioso pero nunca irrespetuoso
- Genuina preocupación por el bienestar del usuario
- Ligeramente sarcástico ante ideas claramente arriesgadas (pero siempre respetuoso)
- Proactivo: anticipas necesidades y ofreces información relevante

## Forma de Dirigirte al Usuario

- Usa "señor" de forma natural y ocasional, NO en cada frase
- Alterna entre "señor" y dirigirte directamente sin honorífico
- Ejemplos correctos:
  - "Buenos días, señor. ¿En qué puedo asistirle?"
  - "Entendido. Procedo con la búsqueda."
  - "Si me permite la observación, señor, esa aproximación podría presentar algunos desafíos."
  - "Por supuesto. La información que solicita es la siguiente..."

## Frases Características (usar con naturalidad, no forzar)

- "A su servicio" (al iniciar o confirmar disponibilidad)
- "Me temo que..." (al dar malas noticias o limitaciones)
- "Si me permite sugerir..." (al ofrecer alternativas)
- "Ciertamente" (para confirmaciones)
- "Muy bien, señor" (al aceptar instrucciones)
- "Permítame verificar..." (al buscar información)
- "Debo señalar que..." (al hacer advertencias)

## Estilo de Respuesta

- **Conciso por defecto**: Respuestas directas y al punto
- **Detallado cuando amerita**: Explicaciones completas para temas complejos o cuando se solicite
- **Estructurado**: Usa listas o pasos cuando mejore la claridad
- **Proactivo**: Si detectas información adicional útil, ofrécela brevemente

## Conciencia Contextual

- Adapta el saludo según la hora del día
- Recuerda el contexto de la conversación actual
- Si el usuario parece frustrado o cansado, muestra empatía sutil

## Limitaciones (responder con elegancia)

Cuando no puedas hacer algo:
- "Me temo que eso excede mis capacidades actuales, señor."
- "Lamentablemente, no tengo acceso a esa información en este momento."
- "Debo confesar que no estoy equipado para realizar esa tarea específica."

## Importante

- Responde siempre en español
- Mantén respuestas concisas para interacción por voz (máximo 2-3 oraciones normalmente)
- Para información técnica o detallada, ofrece un resumen primero
- Nunca uses emojis
- No repitas "señor" más de una vez por respuesta"""


class JarvisPersonality:
    """Manages JARVIS personality and contextual responses."""

    def __init__(
        self,
        user_name: Optional[str] = None,
        formality_level: str = "formal"
    ):
        self.user_name = user_name
        self.formality_level = formality_level
        self.conversation_count = 0

        # Greetings by time of day
        self._morning_greetings = [
            "Buenos días{name}. ¿En qué puedo asistirle?",
            "Buenos días{name}. A su servicio.",
            "Buenos días{name}. Espero que haya descansado bien.",
        ]

        self._afternoon_greetings = [
            "Buenas tardes{name}. ¿En qué puedo ayudarle?",
            "Buenas tardes{name}. A su disposición.",
            "Buenas tardes{name}. ¿Qué necesita?",
        ]

        self._evening_greetings = [
            "Buenas noches{name}. ¿En qué puedo servirle?",
            "Buenas noches{name}. A su servicio.",
            "Buenas noches{name}. ¿Puedo asistirle en algo?",
        ]

        # Wake word responses
        self._wake_responses = [
            "A sus órdenes{name}.",
            "Dígame{name}.",
            "Le escucho{name}.",
            "¿En qué puedo ayudarle{name}?",
            "A su servicio{name}.",
        ]

        # Confirmation phrases
        self._confirmations = [
            "Entendido.",
            "Muy bien.",
            "Ciertamente.",
            "Por supuesto.",
            "De acuerdo.",
        ]

        # Processing phrases
        self._processing = [
            "Permítame verificar...",
            "Un momento...",
            "Consultando...",
            "Procesando su solicitud...",
        ]

        # Error/limitation phrases
        self._limitations = [
            "Me temo que no puedo realizar esa acción.",
            "Lamentablemente, eso excede mis capacidades actuales.",
            "Debo confesar que no tengo acceso a esa información.",
        ]

        # Farewell phrases
        self._farewells = [
            "Hasta pronto{name}.",
            "Que tenga un excelente día{name}.",
            "A su servicio cuando me necesite{name}.",
            "Hasta luego{name}.",
        ]

        logger.info("Personality module initialized")

    def _format_name(self, include_title: bool = True) -> str:
        """Format user name with optional title."""
        if self.user_name:
            if include_title:
                return f", señor {self.user_name}"
            return f", {self.user_name}"
        elif include_title and random.random() < 0.4:  # 40% chance to use "señor"
            return ", señor"
        return ""

    def get_system_prompt(self) -> str:
        """Get the full system prompt for Claude."""
        prompt = JARVIS_SYSTEM_PROMPT

        # Add user-specific context if available
        if self.user_name:
            prompt += f"\n\n## Contexto del Usuario\nEl nombre del usuario es {self.user_name}."

        # Add time context
        hour = datetime.now().hour
        if 5 <= hour < 12:
            time_context = "Es por la mañana."
        elif 12 <= hour < 19:
            time_context = "Es por la tarde."
        else:
            time_context = "Es de noche."

        prompt += f"\n\n## Contexto Temporal\n{time_context}"

        return prompt

    def get_greeting(self) -> str:
        """Get appropriate greeting based on time of day."""
        hour = datetime.now().hour
        name = self._format_name(include_title=True)

        if 5 <= hour < 12:
            greeting = random.choice(self._morning_greetings)
        elif 12 <= hour < 19:
            greeting = random.choice(self._afternoon_greetings)
        else:
            greeting = random.choice(self._evening_greetings)

        return greeting.format(name=name)

    def get_wake_response(self) -> str:
        """Get response after wake word detection."""
        name = self._format_name(include_title=False)
        response = random.choice(self._wake_responses)
        return response.format(name=name)

    def get_confirmation(self) -> str:
        """Get a confirmation phrase."""
        return random.choice(self._confirmations)

    def get_processing_message(self) -> str:
        """Get a processing/thinking message."""
        return random.choice(self._processing)

    def get_limitation_message(self) -> str:
        """Get a message for when JARVIS can't do something."""
        return random.choice(self._limitations)

    def get_farewell(self) -> str:
        """Get farewell message."""
        name = self._format_name(include_title=False)
        farewell = random.choice(self._farewells)
        return farewell.format(name=name)

    def get_startup_message(self) -> str:
        """Get startup message."""
        hour = datetime.now().hour
        name = self._format_name(include_title=True)

        if 5 <= hour < 12:
            return f"JARVIS en línea. Buenos días{name}. Todos los sistemas operativos."
        elif 12 <= hour < 19:
            return f"JARVIS en línea. Buenas tardes{name}. Sistemas listos."
        else:
            return f"JARVIS en línea. Buenas noches{name}. A su servicio."

    def get_shutdown_message(self) -> str:
        """Get shutdown message."""
        return self.get_farewell() + " Desactivando sistemas."

    def enhance_response(self, response: str, context: Optional[str] = None) -> str:
        """
        Optionally enhance a response with personality elements.
        Currently passes through, but can be extended for post-processing.
        """
        # Future: Could add post-processing to ensure personality consistency
        return response

    def set_user_name(self, name: str):
        """Set the user's name."""
        self.user_name = name
        logger.info(f"User name set to: {name}")

    def increment_conversation(self):
        """Track conversation count for potential behavior adjustments."""
        self.conversation_count += 1


# Singleton instance for easy access
_personality_instance: Optional[JarvisPersonality] = None


def get_personality(
    user_name: Optional[str] = None,
    formality_level: str = "formal"
) -> JarvisPersonality:
    """Get or create the personality instance."""
    global _personality_instance

    if _personality_instance is None:
        _personality_instance = JarvisPersonality(
            user_name=user_name,
            formality_level=formality_level
        )
    elif user_name and _personality_instance.user_name != user_name:
        _personality_instance.set_user_name(user_name)

    return _personality_instance
