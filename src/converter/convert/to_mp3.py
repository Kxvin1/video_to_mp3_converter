import pika
import json
import tempfile
import os
from bson.objectid import ObjectId
import moviepy.editor


def start(message, fs_videos, fs_mp3s, channel):
    # '.loads' convert json to python object
    message = json.loads(message)

    # empty temp file
    tf = tempfile.NamedTemporaryFile()
    # video contents, get it from gridFS
    out = fs_videos.get(ObjectId(message["video_fid"]))
    # add video contents to empty file
    tf.write(out.read())
    # create audio from temp video file
    audio = moviepy.editor.VideoFileClip(tf.name).audio
    # close automatically deletes so no clean up needed
    tf.close()

    # write audio to the file
    tf_path = tempfile.gettempdir() + f"/{message['video_fid']}.mp3"
    audio.write_audiofile(tf_path)

    # save file to mongo
    f = open(tf_path, "rb")
    data = f.read()
    fid = fs_mp3s.put(data)
    f.close()
    # manually delete the temp file
    os.remove(tf_path)

    # convert 'fid' to string because the 'fid' that comes from fs_mp3s.put(data) is an object
    message["mp3_fid"] = str(fid)

    # put 'message' on a new queue, the mp3_queue
    try:
        channel.basic_publish(
            exchange="",
            routing_key=os.environ.get("MP3_QUEUE"),
            # '.dumps' converts the python object to json
            body=json.dumps(message),
            # make sure the message is persisted til it is processed
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:

        fs_mp3s.delete(fid)
        return "failed to publish message"
