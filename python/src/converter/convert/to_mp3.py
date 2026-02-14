import json
import logging
import os
import tempfile

import moviepy as mp
import pika
from bson.objectid import ObjectId

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def start(message, fs_videos, fs_mp3s, channel):
    temp_video_path = None
    temp_mp3_path = None
    video_fid = None
    mp3_fid = None
    video_clip = None

    try:
        # Parse the message
        try:
            message = json.loads(message)
        except json.JSONDecodeError as err:
            error_msg = f"Invalid JSON message: {err}"
            logger.error(error_msg)
            return error_msg, 400

        # Validate message structure
        if "video_fid" not in message:
            error_msg = "Missing video_fid in message"
            logger.error(error_msg)
            return error_msg, 400
        if "username" not in message:
            error_msg = "Missing username in message"
            logger.error(error_msg)
            return error_msg, 400

        video_fid = message["video_fid"]
        username = message["username"]
        logger.info(
            f"Processing video conversion for user: {username}, video_fid: {video_fid}"
        )

        # Validate ObjectId format
        try:
            video_object_id = ObjectId(video_fid)
        except Exception as err:
            error_msg = f"Invalid video_fid format: {err}"
            logger.error(error_msg)
            return error_msg, 400

        # Create temporary file for video
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp_video_path = temp_file.name
            temp_file.close()
        except Exception as err:
            error_msg = f"Failed to create temporary file: {err}"
            logger.error(error_msg)
            return error_msg, 500

        # Get the video from the database
        try:
            logger.info(f"Retrieving video {video_fid} from database")
            video = fs_videos.get(video_object_id)
            with open(temp_video_path, "wb") as f:
                f.write(video.read())
            logger.info(f"Video {video_fid} retrieved successfully")
        except Exception as err:
            error_msg = f"Failed to retrieve video from database: {err}"
            logger.error(error_msg)
            return error_msg, 500

        # Convert the video to mp3
        temp_mp3_path = temp_video_path.replace(".mp4", ".mp3")
        try:
            logger.info(f"Starting video to mp3 conversion for {video_fid}")
            video_clip = mp.VideoFileClip(temp_video_path)

            if video_clip.audio is None:
                error_msg = "Video has no audio track"
                logger.warning(f"{error_msg} for video {video_fid}")
                return error_msg, 400

            video_clip.audio.write_audiofile(temp_mp3_path, logger=None)
            logger.info(f"Video {video_fid} converted to mp3 successfully")

        except Exception as err:
            error_msg = f"Failed to convert video to mp3: {err}"
            logger.error(error_msg)
            return error_msg, 500
        finally:
            # Always close the video clip to free resources
            if video_clip:
                try:
                    video_clip.close()
                except Exception as err:
                    logger.warning(f"Failed to close video clip: {err}")

        # Store the mp3 in the database
        try:
            logger.info(f"Storing mp3 for video {video_fid} in database")
            with open(temp_mp3_path, "rb") as mp3_file:
                mp3_fid = fs_mp3s.put(mp3_file)
            message["mp3_fid"] = str(mp3_fid)
            logger.info(f"MP3 stored successfully with fid: {mp3_fid}")
        except Exception as err:
            error_msg = f"Failed to store mp3 in database: {err}"
            logger.error(error_msg)
            return error_msg, 500

        # Get MP3_QUEUE from environment
        mp3_queue = os.getenv("MP3_QUEUE")
        if not mp3_queue:
            error_msg = "MP3_QUEUE environment variable not set"
            logger.error(error_msg)
            # Clean up the mp3 we just stored
            if mp3_fid:
                try:
                    fs_mp3s.delete(ObjectId(mp3_fid))
                except Exception as err:
                    logger.error(f"Failed to delete mp3 during cleanup: {err}")
            return error_msg, 500

        # Publish the message to the queue
        try:
            logger.info(f"Publishing message to queue {mp3_queue}")
            channel.basic_publish(
                exchange="",
                routing_key=mp3_queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                ),
            )
            logger.info(f"Conversion completed successfully for video {video_fid}")
        except Exception as err:
            error_msg = f"Failed to publish message: {err}"
            logger.error(error_msg)
            # Clean up the mp3 we just stored
            if mp3_fid:
                try:
                    fs_mp3s.delete(ObjectId(mp3_fid))
                    logger.info(f"Deleted mp3 {mp3_fid} after publish failure")
                except Exception as cleanup_err:
                    logger.error(f"Failed to delete mp3 during cleanup: {cleanup_err}")
            return error_msg, 500

        return None

    except Exception as err:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error during conversion: {err}"
        logger.exception(error_msg)

        # Clean up mp3 if it was stored
        if mp3_fid:
            try:
                fs_mp3s.delete(ObjectId(mp3_fid))
                logger.info(f"Deleted mp3 {mp3_fid} after unexpected error")
            except Exception as cleanup_err:
                logger.error(f"Failed to delete mp3 during cleanup: {cleanup_err}")

        return error_msg, 500

    finally:
        # Clean up temporary files - always runs
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
                logger.debug(f"Deleted temporary video file: {temp_video_path}")
            except Exception as err:
                logger.warning(f"Failed to delete temporary video file: {err}")

        if temp_mp3_path and os.path.exists(temp_mp3_path):
            try:
                os.unlink(temp_mp3_path)
                logger.debug(f"Deleted temporary mp3 file: {temp_mp3_path}")
            except Exception as err:
                logger.warning(f"Failed to delete temporary mp3 file: {err}")
