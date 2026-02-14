import json
import os
import tempfile

import moviepy.editor as mp
import pika
from bson.objectid import ObjectId


def start(message, fs_videos, fs_mp3s, channel):
    temp_file = None
    video_fid = None
    mp3_fid = None

    try:
        # Parse the message
        try:
            message = json.loads(message)
        except json.JSONDecodeError as err:
            return f"Invalid JSON message: {err}", 400

        # Validate message structure
        if "video_fid" not in message:
            return "Missing video_fid in message", 400
        if "username" not in message:
            return "Missing username in message", 400

        video_fid = message["video_fid"]

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")

        # Get the video from the database
        try:
            video = fs_videos.get(ObjectId(video_fid))
            temp_file.write(video.read())
            temp_file.flush()
        except Exception as err:
            return f"Failed to retrieve video from database: {err}", 500

        # Convert the video to mp3
        mp3_temp_path = temp_file.name.replace(".mp4", ".mp3")
        try:
            video_clip = mp.VideoFileClip(temp_file.name)
            if video_clip.audio is None:
                video_clip.close()
                return "Video has no audio track", 400
            video_clip.audio.write_audiofile(mp3_temp_path, logger=None)
            video_clip.close()
        except Exception as err:
            return f"Failed to convert video to mp3: {err}", 500

        # Store the mp3 in the database
        try:
            with open(mp3_temp_path, "rb") as mp3_file:
                mp3_fid = fs_mp3s.put(mp3_file)
            message["mp3_fid"] = str(mp3_fid)
        except Exception as err:
            return f"Failed to store mp3 in database: {err}", 500

        # Get MP3_QUEUE from environment
        mp3_queue = os.getenv("MP3_QUEUE")
        if not mp3_queue:
            if mp3_fid:
                fs_mp3s.delete(ObjectId(mp3_fid))
            return "MP3_QUEUE environment variable not set", 500

        # Publish the message to the queue
        try:
            channel.basic_publish(
                exchange="",
                routing_key=mp3_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
        except Exception as err:
            if mp3_fid:
                fs_mp3s.delete(ObjectId(mp3_fid))
            return f"Failed to publish message: {err}", 500

        return None

    except Exception as err:
        # Catch-all for unexpected errors
        if mp3_fid:
            try:
                fs_mp3s.delete(ObjectId(mp3_fid))
            except Exception:
                pass
        return f"Unexpected error during conversion: {err}", 500

    finally:
        # Clean up temporary files
        if temp_file:
            try:
                temp_file.close()
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                mp3_temp_path = temp_file.name.replace(".mp4", ".mp3")
                if os.path.exists(mp3_temp_path):
                    os.unlink(mp3_temp_path)
            except Exception:
                pass
