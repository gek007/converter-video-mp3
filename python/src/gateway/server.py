import json
import os
from datetime import datetime
from pathlib import Path

import gridfs
import pika

# from auth import validate
# from auth_svc import access
from dotenv import load_dotenv
from flask import Flask
from flask_pymongo import PyMongo

# from storage import util

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=BASE_DIR / "../../.env")
load_dotenv(dotenv_path=BASE_DIR / "../../.env.local", override=True)


# Initialize Flask server and MongoDB connection
server = Flask(__name__)
server.config["MONGO_URI"] = os.getenv(
    "MONGO_URI", "mongodb://host.minikube.internal:27017/gateway"
)

print("MONGO_URI:", server.config["MONGO_URI"])

# Set up MongoDB connection
mongo = PyMongo(server)
fs = gridfs.GridFS(mongo.db)

# Set up RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()


if __name__ == "__main__":
    pass
