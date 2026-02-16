"""Text summarization using OpenAI GPT-4.1 API."""
import logging
import time

from openai import OpenAI

from config import Config

logger = logging.getLogger(__name__)


class SummarizationError(Exception):
    """Custom exception for summarization errors."""

    pass


class SummarizationService:
    """Service for summarizing text using OpenAI GPT-4.1 API."""

    def __init__(self):
        """Initialize summarization service with OpenAI client."""
        Config.validate()
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.OPENAI_CHAT_MODEL

    def summarize_text(self, transcript: str) -> tuple[str, int]:
        """
        Summarize transcript text using GPT-4.1 API.

        Args:
            transcript: Transcript text to summarize

        Returns:
            Tuple of (summary text, processing time in milliseconds)

        Raises:
            SummarizationError: If summarization fails
        """
        start_time = time.time()

        try:
            logger.info(f"Summarizing transcript: {len(transcript)} chars")

            # Create prompt for summarization
            prompt = f"""Please provide a concise summary of the following transcript.
Focus on key points, main topics, and important conclusions.

Transcript:
{transcript}

Summary:"""

            # Call OpenAI Chat Completions API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that summarizes transcripts accurately and concisely."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=Config.OPENAI_MAX_TOKENS,
                temperature=Config.OPENAI_TEMPERATURE
            )

            summary = response.choices[0].message.content
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log token usage for cost tracking
            usage = response.usage
            logger.info(
                f"Summary generated: {len(summary)} chars "
                f"in {processing_time_ms}ms "
                f"(tokens: {usage.prompt_tokens} input, {usage.completion_tokens} output, {usage.total_tokens} total)"
            )

            return summary, processing_time_ms

        except Exception as err:
            logger.error(f"Summarization failed: {err}")
            raise SummarizationError(f"Failed to summarize text: {err}")
