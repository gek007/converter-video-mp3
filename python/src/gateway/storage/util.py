import json

import pika


# channel is the rabbitmq channel
# fs is the gridfs instance
# access is the access object
def upload(file, fs, channel, access):
    try:
        fid = fs.put(file)
    except Exception:
        return "Internal Server Error", 500

    message = {"video_fid": str(fid), "mp3_fid": None, "username": access["username"]}

    # publish the message to the queue
    try:
        channel.basic_publish(
            exchange="",
            routing_key="video",
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception:
        fs.delete(fid)
        return "Internal Server Error", 500

    # return the message
    return message
