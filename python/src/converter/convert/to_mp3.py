import json
import os
import tempfile

import moviepy.editor as mp
import pika
from bson.objectid import ObjectId


def start(message, fs_videos, fs_mp3s, channel):

    # get the video fid and username from the message
    message = json.loads(message)

    # empty temp file
    temp_file = tempfile.NamedTemporaryFile(delete=True)

    # get the video from the database
    video_fid = message["video_fid"]
    video = fs_videos.get(ObjectId(video_fid))
    temp_file.write(video.read())

    # convert the video to mp3
    video = mp.VideoFileClip(temp_file.name)
    video.audio.write_audiofile(temp_file.name.replace("mp4", "mp3"))

    # store the mp3 in the database
    mp3_fid = fs_mp3s.put(temp_file)
    message["mp3_fid"] = str(mp3_fid)

    # delete the temporary file
    temp_file.close()

    # publish the message to the queue
    channel.basic_publish(
        exchange="",
        routing_key=os.getenv("MP3_QUEUE"),
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        ),
    )
    return message
