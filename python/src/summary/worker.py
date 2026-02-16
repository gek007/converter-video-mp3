"""Summary service worker for processing MP3 files."""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Optional

import gridfs
import pika
from bson.objectid import ObjectId
from pymongo import MongoClient

from config import Config
from transcribe import TranscriptionService, TranscriptionError
from summarize import SummarizationService, SummarizationError

# Configure logging
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SummaryWorker:
    """Worker for processing MP3 files and generating summaries."""

    def __init__(self):
        """Initialize summary worker with services and connections."""
        self.config = Config
        self.transcription_service = TranscriptionService()
        self.summarization_service = SummarizationService()

        # Connect to MongoDB
        self.mongo_client = MongoClient(self.config.MONGO_URI)
        self.mongo_client.server_info()
        logger.info("Connected to MongoDB successfully")

        # Extract database name from URI
        db_name = self.config.MONGO_URI.split("/")[-1] if "/" in self.config.MONGO_URI else "gateway"
        self.db = self.mongo_client[db_name]
        logger.info(f"Using database: {db_name}")

        # Connect to GridFS
        self.fs_mp3s = gridfs.GridFS(self.db)
        self.summaries_collection = self.db.summaries

        # Connect to RabbitMQ
        credentials = pika.PlainCredentials(
            self.config.RABBITMQ_USER,
            self.config.RABBITMQ_PASS
        )
        parameters = pika.ConnectionParameters(
            host=self.config.RABBITMQ_HOST,
            port=self.config.RABBITMQ_PORT,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        logger.info("Connected to RabbitMQ successfully")

        # Declare queues
        self.channel.queue_declare(queue=self.config.MP3_QUEUE, durable=True)
        self.channel.queue_declare(queue=self.config.SUMMARY_QUEUE, durable=True)

    def process_message(self, body: bytes) -> Optional[str]:
        """
        Process message from MP3 queue.

        Args:
            body: Message body containing JSON with mp3_fid and username

        Returns:
            Error message if processing failed, None if successful
        """
        try:
            # Parse message
            message = json.loads(body)
            mp3_fid = message.get("mp3_fid")
            video_fid = message.get("video_fid")
            username = message.get("username")

            if not mp3_fid or not video_fid or not username:
                error_msg = "Missing required fields in message"
                logger.error(error_msg)
                return error_msg

            logger.info(
                f"Processing summary for user: {username}, "
                f"video_fid: {video_fid}, mp3_fid: {mp3_fid}"
            )

            # Retrieve MP3 from GridFS
            logger.info(f"Retrieving MP3 {mp3_fid} from database")
            try:
                mp3_object_id = ObjectId(mp3_fid)
                mp3_data = self.fs_mp3s.get(mp3_object_id).read()
                logger.info(f"MP3 {mp3_fid} retrieved successfully ({len(mp3_data)} bytes)")
            except Exception as err:
                error_msg = f"Failed to retrieve MP3 from database: {err}"
                logger.error(error_msg)
                return error_msg

            # Transcribe audio
            logger.info(f"Starting transcription for MP3 {mp3_fid}")
            try:
                transcript, transcript_time_ms = self.transcription_service.transcribe_audio(
                    mp3_data,
                    filename=f"{mp3_fid}.mp3"
                )
            except TranscriptionError as err:
                error_msg = f"Transcription failed: {err}"
                logger.error(error_msg)
                return error_msg

            # Summarize transcript
            logger.info(f"Starting summarization for MP3 {mp3_fid}")
            try:
                summary, summary_time_ms = self.summarization_service.summarize_text(transcript)
            except SummarizationError as err:
                error_msg = f"Summarization failed: {err}"
                logger.error(error_msg)
                return error_msg

            # Store summary in MongoDB
            logger.info(f"Storing summary for MP3 {mp3_fid} in database")
            total_processing_time_ms = transcript_time_ms + summary_time_ms

            try:
                summary_doc = {
                    "mp3_fid": mp3_object_id,
                    "video_fid": ObjectId(video_fid),
                    "username": username,
                    "transcript": transcript,
                    "summary": summary,
                    "transcript_length": len(transcript),
                    "summary_length": len(summary),
                    "processing_time_ms": total_processing_time_ms,
                    "created_at": datetime.utcnow(),
                    "status": "completed"
                }
                result = self.summaries_collection.insert_one(summary_doc)
                summary_fid = str(result.inserted_id)
                logger.info(f"Summary stored successfully with fid: {summary_fid}")
            except Exception as err:
                error_msg = f"Failed to store summary in database: {err}"
                logger.error(error_msg)
                return error_msg

            # Publish message to summary queue
            logger.info(f"Publishing message to queue {self.config.SUMMARY_QUEUE}")
            summary_message = {
                "video_fid": video_fid,
                "mp3_fid": mp3_fid,
                "summary_fid": summary_fid,
                "username": username
            }

            self.channel.basic_publish(
                exchange="",
                routing_key=self.config.SUMMARY_QUEUE,
                body=json.dumps(summary_message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )

            logger.info(
                f"Summary processing completed successfully for video {video_fid} "
                f"(total time: {total_processing_time_ms}ms)"
            )

            return None

        except json.JSONDecodeError as err:
            error_msg = f"Invalid JSON message: {err}"
            logger.error(error_msg)
            return error_msg

        except Exception as err:
            error_msg = f"Unexpected error during processing: {err}"
            logger.exception(error_msg)
            return error_msg

    def callback(self, ch, method, properties, body):
        """
        RabbitMQ message callback.

        Args:
            ch: Channel
            method: Method
            properties: Properties
            body: Message body
        """
        try:
            logger.info(f"Received message: {body[:100]}...")  # Log first 100 chars

            error = self.process_message(body)

            if error:
                logger.error(f"Processing failed: {error}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                logger.info("Message processed successfully")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as callback_err:
            logger.exception(f"Unexpected error in callback: {callback_err}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def start(self):
        """Start consuming messages from the MP3 queue."""
        try:
            logger.info(f"Starting summary service worker")
            logger.info(f"Listening on queue: {self.config.MP3_QUEUE}")

            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(
                queue=self.config.MP3_QUEUE,
                on_message_callback=self.callback
            )

            logger.info("Waiting for messages. To exit press CTRL+C")
            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Shutting down worker")
            self.channel.stop_consuming()
            self.connection.close()
            self.mongo_client.close()

        except Exception as err:
            logger.error(f"Worker error: {err}")
            raise


def main():
    """Main entry point."""
    try:
        worker = SummaryWorker()
        worker.start()
    except Exception as err:
        logger.error(f"Failed to start worker: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
