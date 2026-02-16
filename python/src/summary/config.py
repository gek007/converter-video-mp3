"""Configuration management for summary service."""
import os
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local", override=True)


class Config:
    """Summary service configuration."""

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:admin123@mongodb:27017/gateway?authSource=admin")

    # RabbitMQ
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "admin")
    RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    MP3_QUEUE = os.getenv("MP3_QUEUE", "mp3")
    SUMMARY_QUEUE = os.getenv("SUMMARY_QUEUE", "summary")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_WHISPER_MODEL = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")
    OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4-turbo")
    OPENAI_MAX_TOKENS = int(os.getenv("OPENAI_MAX_TOKENS", "500"))
    OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", "0.5"))

    # Processing
    MAX_AUDIO_SIZE_MB = int(os.getenv("MAX_AUDIO_SIZE_MB", "25"))
    TRANSCRIPT_TIMEOUT = int(os.getenv("TRANSCRIPT_TIMEOUT", "300"))
    SUMMARY_TIMEOUT = int(os.getenv("SUMMARY_TIMEOUT", "60"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required")

        if cls.MAX_AUDIO_SIZE_MB > 25:
            raise ValueError("MAX_AUDIO_SIZE_MB cannot exceed 25 (Whisper API limit)")
