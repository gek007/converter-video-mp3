import json
import os

import gridfs
import pika
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_file
from flask_pymongo import PyMongo

from auth import validate
from auth_srv import access
from storage import util

load_dotenv(".env")
load_dotenv(".env.local", override=True)

# Initialize Flask server and MongoDB connection
server = Flask(__name__)

# Set up MongoDB connection
mongo_video = PyMongo(server, uri="mongodb://host.minikube.internal:27017/videos")
mongo_mp3 = PyMongo(server, uri="mongodb://host.minikube.internal:27017/mp3s")

fs_video = gridfs.GridFS(mongo_video.db)
fs_mp3 = gridfs.GridFS(mongo_mp3.db)

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
                blocked_connection_timeout=300,
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
        print(f"[DEBUG] Token validation failed: {err}")
        return jsonify({"error": err[0]}), err[1]

    access_data = json.loads(access_token)
    print(f"[DEBUG] Access data: {access_data}")

    if access_data["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            print("[DEBUG] Invalid file count")
            return jsonify({"error": "Exactly one file required"}), 400

        try:
            print("[DEBUG] Getting RabbitMQ channel")
            channel = get_rabbitmq_channel()
            print("[DEBUG] Got RabbitMQ channel")

            for _, file in request.files.items():
                print(f"[DEBUG] Uploading file: {file.filename}")
                result = util.upload(file, fs, channel, access_data)
                print(f"[DEBUG] Upload result: {result}")

                # Check if result is an error tuple (message, status_code)
                if isinstance(result, tuple) and len(result) == 2:
                    print("[DEBUG] Upload error tuple detected")
                    return jsonify({"error": result[0]}), result[1]

            print("[DEBUG] Upload successful")
            return jsonify({"message": "Upload successful"}), 200
        except Exception as e:
            print(f"[DEBUG] Exception in upload: {str(e)}")
            import traceback

            traceback.print_exc()
            return jsonify({"error": f"Upload failed: {str(e)}"}), 500
    else:
        print("[DEBUG] User not authorized")
        return jsonify({"error": "Not authorized"}), 401


@server.route("/download", methods=["GET"])
def download():
    access_token, err = validate.token(request)

    if err:
        print(f"[DEBUG] Token validation failed: {err}")
        return jsonify({"error": err[0]}), err[1]

    access_data = json.loads(access_token)
    print(f"[DEBUG] Access data: {access_data}")

    if access_data["admin"]:
        fid_string = request.args.get("fid")
        if not fid_string:
            return jsonify({"error": "fid is required"}), 400

        try:
            out = fs_mp3.get(ObjectId(fid_string))
            return send_file(out, download_name=f"{fid_string}.mp3")
        except Exception as err:
            print(f"[DEBUG] Error downloading file: {err}")
            return jsonify({"error": f"Invalid fid: {err}"}), 400

    else:
        return jsonify({"error": "Not authorized"}), 401


def my_test_func():
    return jsonify({"message": "Hello, World!"}), 200


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080, debug=True)
