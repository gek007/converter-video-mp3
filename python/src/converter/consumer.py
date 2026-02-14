import os
import sys
import time

import gridfs
import pika
from convert import to_mp3
from pymongo import MongoClient


def main():
    client = MongoClient("host.minikube.internal:27017")
    db_videos = client.videos
