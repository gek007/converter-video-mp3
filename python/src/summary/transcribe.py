"""Audio transcription using OpenAI Whisper API."""
import logging
import os
import tempfile
from typing import Tuple

import httpx
from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Custom exception for transcription errors."""

    pass


class TranscriptionService:
    """Service for transcribing audio using OpenAI Whisper API."""

    def __init__(self):
        """Initialize transcription service with OpenAI client."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_WHISPER_MODEL

    async def transcribe_audio(self, audio_data: bytes, filename: str = "audio.mp3") -> Tuple[str, int]:
        """
        Transcribe audio data using Whisper API.

        Args:
            audio_data: Binary audio data (MP3 format)
            filename: Original filename for logging

        Returns:
            Tuple of (transcript text, processing time in milliseconds)

        Raises:
            TranscriptionError: If transcription fails
        """
        import time

        start_time = time.time()

        try:
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name

            logger.info(f"Transcribing audio file: {filename} (size: {len(audio_data)} bytes)")

            # Check file size limit
            size_mb = len(audio_data) / (1024 * 1024)
            if size_mb > Config.MAX_AUDIO_SIZE_MB:
                raise TranscriptionError(
                    f"Audio file too large: {size_mb:.2f}MB exceeds limit of {Config.MAX_AUDIO_SIZE_MB}MB"
                )

            # Transcribe using Whisper API
            with open(temp_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="text"
                )

            transcript = response
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Transcription completed: {len(transcript)} chars "
                f"in {processing_time_ms}ms"
            )

            return transcript, processing_time_ms

        except Exception as err:
            logger.error(f"Transcription failed for {filename}: {err}")
            raise TranscriptionError(f"Failed to transcribe audio: {err}")

        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                    logger.debug(f"Deleted temporary file: {temp_path}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete temporary file: {cleanup_err}")
