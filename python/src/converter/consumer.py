import os
import sys

import gridfs
import pika
from convert import to_mp3
from pymongo import MongoClient


def main():
    # Use the same database configuration as gateway
    mongo_uri = os.getenv("MONGO_URI", "mongodb://host.minikube.internal:27017/gateway")
    client = MongoClient(mongo_uri)
    
    # Extract database name from URI, default to 'gateway'
    db_name = mongo_uri.split('/')[-1] if '/' in mongo_uri else 'gateway'
    db_videos = client[db_name]
    db_mp3s = client[db_name]

    # connect to gridfs
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # connect to rabbitmq
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="rabbitmq"))
    channel = connection.channel()

    def callback(ch, method, properties, body):
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)
        if err:
            ch.basic_nack(delivery_tag=method.delivery_tag)
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=os.getenv("VIDEO_QUEUE"), on_message_callback=callback)

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
