import os
import sys

import gridfs
import pika
from convert import to_mp3
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(".env")
load_dotenv(".env.local", override=True)


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

    # Connect to MongoDB
    client = MongoClient(mongo_uri)
    
    # Extract database name from URI, default to 'gateway'
    db_name = mongo_uri.split('/')[-1] if '/' in mongo_uri else 'gateway'
    db_videos = client[db_name]
    db_mp3s = client[db_name]

    # Connect to GridFS
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # Connect to RabbitMQ
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=video_queue, on_message_callback=callback)

    print("Waiting for messages. To exit press CTRL+C")
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
