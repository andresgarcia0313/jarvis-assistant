"""
JARVIS Claude CLI Bridge Module
Handles communication with Claude CLI
"""

import subprocess
import logging
import shutil
import tempfile
import os
from typing import Optional

logger = logging.getLogger(__name__)


class ClaudeBridge:
    """Bridge to interact with Claude CLI."""

    def __init__(
        self,
        command: str = "claude",
        timeout: int = 60,
        system_prompt: Optional[str] = None
    ):
        self.command = command
        self.timeout = timeout
        self.system_prompt = system_prompt

        # Verify claude CLI is available
        if not shutil.which(command):
            raise RuntimeError(
                f"Claude CLI not found. Make sure '{command}' is installed and in PATH."
            )

        logger.info("Claude CLI bridge initialized")

    def set_system_prompt(self, prompt: str):
        """Set or update the system prompt."""
        self.system_prompt = prompt
        logger.debug("System prompt updated")

    def send(self, message: str) -> Optional[str]:
        """
        Send a message to Claude CLI and get response.

        Args:
            message: User message to send

        Returns:
            Claude's response or None on error
        """
        if not message:
            return None

        temp_file = None
        try:
            # Build command
            cmd = [self.command, "-p", message]

            # Add system prompt if configured
            # Use temp file for long prompts to avoid command line limits
            if self.system_prompt:
                if len(self.system_prompt) > 500:
                    # Write to temp file for long prompts
                    temp_file = tempfile.NamedTemporaryFile(
                        mode='w',
                        suffix='.txt',
                        delete=False
                    )
                    temp_file.write(self.system_prompt)
                    temp_file.close()
                    cmd.extend(["--system-prompt", temp_file.name])
                else:
                    cmd.extend(["--system", self.system_prompt])

            logger.debug(f"Sending to Claude: {message[:100]}...")

            # Execute
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                logger.error(f"Claude CLI error: {result.stderr}")
                return None

            response = result.stdout.strip()
            logger.debug(f"Claude response: {response[:100]}...")

            return response

        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI timeout after {self.timeout}s")
            return None
        except Exception as e:
            logger.error(f"Error communicating with Claude: {e}")
            return None
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                os.unlink(temp_file.name)

    def send_with_context(
        self,
        message: str,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Send a message with additional context.

        Args:
            message: User message
            context: Additional context (e.g., conversation history)

        Returns:
            Claude's response
        """
        if context:
            full_message = f"{context}\n\nUsuario: {message}"
        else:
            full_message = message

        return self.send(full_message)

    def check_connection(self) -> bool:
        """
        Check if Claude CLI is working.

        Returns:
            True if CLI is responsive
        """
        try:
            result = subprocess.run(
                [self.command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False


class ConversationManager:
    """Manages conversation history for context."""

    def __init__(self, max_history: int = 10):
        self.history: list[dict] = []
        self.max_history = max_history

    def add_exchange(self, user_message: str, assistant_response: str):
        """Add a conversation exchange."""
        self.history.append({
            "user": user_message,
            "assistant": assistant_response
        })

        # Trim history if needed
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_context(self) -> str:
        """Get conversation history as context string."""
        if not self.history:
            return ""

        lines = []
        for exchange in self.history[-5:]:  # Last 5 exchanges
            lines.append(f"Usuario: {exchange['user']}")
            lines.append(f"JARVIS: {exchange['assistant']}")

        return "\n".join(lines)

    def clear(self):
        """Clear conversation history."""
        self.history.clear()
