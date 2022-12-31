import pika
import sys
import os
import time
import gridfs
from pymongo import MongoClient
from convert import to_mp3


def main():
    client = MongoClient("host.minikube.internal", 27017)

    # these dbs gives us access to db videos that we have in our mongo db
    db_videos = client.videos
    db_mp3s = client.mp3s

    # gridfs
    fs_videos = gridfs.GridFS(db_videos)
    fs_mp3s = gridfs.GridFS(db_mp3s)

    # rabbitmq
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="rabbitmq")
    )

    channel = connection.channel()

    # callback functions params: channel 'ch', method, properties, body
    def callback(ch, method, properties, body):
        # to_mp3 is a package/module we imported
        err = to_mp3.start(body, fs_videos, fs_mp3s, ch)

        # if error, send negative acknowledgement (n-ack) to the channel
        if err:
            # keep messages on the queue if there's a failure to process them so we can process them later
            ch.basic_nack(delivery_tag=method.delivery_tag)
        # else, no issue with conversion
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=os.environ.get("VIDEO_QUEUE"), on_message_callback=callback
    )

    print("Waiting for messages. TO exit press CTRL+C")

    channel.start_consuming()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os.exit(0)
