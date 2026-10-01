from __future__ import annotations

from dataclasses import dataclass
import shutil
import subprocess
from collections.abc import Callable, Sequence
from typing import Any


CommandRunner = Callable[..., subprocess.CompletedProcess[str]]
VoiceHandler = Callable[[str], str]


class VoiceInteractionError(RuntimeError):
    """Base exception for voice interaction failures."""


class VoiceDependencyError(VoiceInteractionError):
    """Raised when a required Termux command is unavailable."""


class VoiceCommandTimeout(VoiceInteractionError):
    """Raised when a voice command does not finish in time."""


class VoiceCommandError(VoiceInteractionError):
    """Raised when a Termux voice command exits unsuccessfully."""


@dataclass(frozen=True, slots=True)
class VoiceConfig:
    """Configuration for the Termux voice interface."""

    speech_command: tuple[str, ...] = ("termux-speech-to-text",)
    tts_command: tuple[str, ...] = ("termux-tts-speak",)
    listen_timeout: float = 60.0
    speak_timeout: float = 30.0
    stop_phrases: tuple[str, ...] = ("exit", "quit", "shutdown")


class VoiceInteraction:
    """
    Small reusable voice I/O layer for Android via Termux:API.

    Responsibilities:
    - capture one spoken utterance
    - speak one text response
    - optionally run a voice conversation loop around a caller-supplied handler

    The layer does not know anything about agents, models, memory, tools, or
    application logic. A caller supplies the handler that turns user text into
    a response.
    """

    def __init__(
        self,
        config: VoiceConfig | None = None,
        *,
        runner: CommandRunner | None = None,
    ) -> None:
        self.config = config or VoiceConfig()
        self._runner = runner or subprocess.run
        self._uses_system_runner = runner is None

        self._validate_config()

    def listen(self) -> str:
        """Capture one spoken utterance and return its normalized text."""
        self._check_dependency(self.config.speech_command)

        completed = self._run_command(
            self.config.speech_command,
            timeout=self.config.listen_timeout,
            operation="speech recognition",
        )

        return completed.stdout.strip()

    def speak(self, text: str) -> None:
        """Speak text through Android TTS."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        text = text.strip()
        if not text:
            return

        self._check_dependency(self.config.tts_command)

        self._run_command(
            (*self.config.tts_command, text),
            timeout=self.config.speak_timeout,
            operation="text to speech",
        )

    def run(self, handler: VoiceHandler) -> None:
        """
        Run a continuous voice-to-voice loop.

        The supplied handler owns all application logic. It receives one
        recognized user utterance and must return the text to speak.
        """
        if not callable(handler):
            raise TypeError("handler must be callable")

        while True:
            user_input = self.listen()

            if not user_input:
                continue

            if self._is_stop_phrase(user_input):
                return

            response = handler(user_input)

            if not isinstance(response, str):
                raise TypeError("handler must return a string")

            self.speak(response)

    def _run_command(
        self,
        command: Sequence[str],
        *,
        timeout: float,
        operation: str,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._runner(
                list(command),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=True,
                shell=False,
            )
        except FileNotFoundError as exc:
            raise VoiceDependencyError(
                f"Required command is unavailable: {command[0]}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise VoiceCommandTimeout(
                f"{operation} timed out after {timeout:g} seconds"
            ) from exc
        except subprocess.CalledProcessError as exc:
            details = (exc.stderr or "").strip()
            message = f"{operation} failed with exit code {exc.returncode}"
            if details:
                message += f": {details}"
            raise VoiceCommandError(message) from exc

    def _check_dependency(self, command: Sequence[str]) -> None:
        if not command:
            raise VoiceDependencyError("Voice command cannot be empty")

        if self._uses_system_runner and shutil.which(command[0]) is None:
            raise VoiceDependencyError(
                f"Required command is unavailable: {command[0]}"
            )

    def _is_stop_phrase(self, text: str) -> bool:
        normalized = " ".join(text.casefold().split())
        return normalized in {
            " ".join(phrase.casefold().split())
            for phrase in self.config.stop_phrases
            if phrase.strip()
        }

    def _validate_config(self) -> None:
        if self.config.listen_timeout <= 0:
            raise ValueError("listen_timeout must be greater than zero")

        if self.config.speak_timeout <= 0:
            raise ValueError("speak_timeout must be greater than zero")

        if not self.config.speech_command:
            raise ValueError("speech_command cannot be empty")

        if not self.config.tts_command:
            raise ValueError("tts_command cannot be empty")
