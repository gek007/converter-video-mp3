import json
import os

import gridfs
import pika
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_pymongo import PyMongo

from auth import validate
from auth_srv import access
from storage import util

load_dotenv(".env")
load_dotenv(".env.local", override=True)


# Initialize Flask server and MongoDB connection
server = Flask(__name__)
server.config["MONGO_URI"] = os.getenv(
    "MONGO_URI", "mongodb://host.minikube.internal:27017/gateway"
)

print("MONGO_URI:", server.config["MONGO_URI"])

# Set up MongoDB connection
mongo = PyMongo(server)
fs = gridfs.GridFS(mongo.db)

# RabbitMQ connection will be lazily initialized
_rabbitmq_connection = None
_rabbitmq_channel = None


def get_rabbitmq_channel():
    """Get or create RabbitMQ channel."""
    global _rabbitmq_connection, _rabbitmq_channel

    if _rabbitmq_channel is None:
        rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
        rabbitmq_user = os.getenv("RABBITMQ_USER", "guest")
        rabbitmq_pass = os.getenv("RABBITMQ_PASS", "guest")
        rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))

        credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
        _rabbitmq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=rabbitmq_host,
                port=rabbitmq_port,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
        )
        _rabbitmq_channel = _rabbitmq_connection.channel()

    return _rabbitmq_channel


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():
    access_token, err = validate.token(request)

    if err:
        return jsonify({"error": err[0]}), err[1]

    access_data = json.loads(access_token)

    if access_data["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return jsonify({"error": "Exactly one file required"}), 400

        try:
            channel = get_rabbitmq_channel()

            for _, file in request.files.items():
                result = util.upload(file, fs, channel, access_data)

                # Check if result is an error tuple (message, status_code)
                if isinstance(result, tuple) and len(result) == 2:
                    return jsonify({"error": result[0]}), result[1]

            return jsonify({"message": "Upload successful"}), 200
        except Exception as e:
            return jsonify({"error": f"Upload failed: {str(e)}"}), 500
    else:
        return jsonify({"error": "Not authorized"}), 401


@server.route("/download", methods=["GET"])
def download():
    pass


def my_test_func():
    return jsonify({"message": "Hello, World!"}), 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
