import logging
import os
import sys

import gridfs
import pika
from convert import to_mp3
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(".env")
load_dotenv(".env.local", override=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    # Load required environment variables
    mongo_uri = os.getenv("MONGO_URI")
    rabbitmq_host = os.getenv("RABBITMQ_HOST")
    video_queue = os.getenv("VIDEO_QUEUE")
    mp3_queue = os.getenv("MP3_QUEUE")

    # Validate required environment variables
    if not mongo_uri:
        raise ValueError("MONGO_URI environment variable is required")
    if not rabbitmq_host:
        raise ValueError("RABBITMQ_HOST environment variable is required")
    if not video_queue:
        raise ValueError("VIDEO_QUEUE environment variable is required")
    if not mp3_queue:
        raise ValueError("MP3_QUEUE environment variable is required")

    logger.info("Starting converter service")
    logger.info(f"MongoDB URI: {mongo_uri}")
    logger.info(f"RabbitMQ Host: {rabbitmq_host}")
    logger.info(f"Video Queue: {video_queue}")
    logger.info(f"MP3 Queue: {mp3_queue}")

    # Connect to MongoDB
    try:
        client = MongoClient(mongo_uri)
        # Test connection
        client.server_info()
        logger.info("Connected to MongoDB successfully")
    except Exception as err:
        logger.error(f"Failed to connect to MongoDB: {err}")
        raise
    
    # Extract database name from URI, default to 'gateway'
    db_name = mongo_uri.split('/')[-1] if '/' in mongo_uri else 'gateway'
    db_videos = client[db_name]
    db_mp3s = client[db_name]
    logger.info(f"Using database: {db_name}")

    # Connect to GridFS
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # Connect to RabbitMQ
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
        channel = connection.channel()
        logger.info("Connected to RabbitMQ successfully")
    except Exception as err:
        logger.error(f"Failed to connect to RabbitMQ: {err}")
        raise

    def callback(ch, method, properties, body):
        try:
            logger.info(f"Received message: {body[:100]}...")  # Log first 100 chars
            err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
            if err:
                logger.error(f"Conversion failed: {err}")
                ch.basic_nack(delivery_tag=method.delivery_tag)
            else:
                logger.info("Message processed successfully")
                ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as callback_err:
            logger.exception(f"Unexpected error in callback: {callback_err}")
            ch.basic_nack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=video_queue, on_message_callback=callback)

    logger.info("Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
