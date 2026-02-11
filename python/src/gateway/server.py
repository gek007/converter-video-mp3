import json
import os

import gridfs
import pika
from dotenv import load_dotenv
from flask import Flask, request
from flask_pymongo import PyMongo

from auth import validate
from auth_srv import access
from storage import util

# from storage import util

# BASE_DIR = Path(__file__).resolve().parent
# load_dotenv(dotenv_path=BASE_DIR / "../../.env")
# load_dotenv(dotenv_path=BASE_DIR / "../../.env.local", override=True)

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

# Set up RabbitMQ connection
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()


@server.route("/login", methods=["POST"])
def login():
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


@server.route("/upload", methods=["POST"])
def upload():

    access, err = validate.token(request)

    access = json.loads(access)

    if access["admin"]:
        if len(request.files) > 1 or len(request.files) < 1:
            return "Too many files", 400

        for _, file in request.files.items():
            err = util.upload(file, fs, channel, access)

            if err:
                return err

        return "success", 200
    else:
        return "Not Authorized", 401


@server.route("/download", methods=["GET"])
def download():
    pass


if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
