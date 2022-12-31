import pika
import json


def upload(f, fs, channel, access):
    try:
        # if this put is successful, a file id object (fid) is going to be returned
        fid = fs.put(f)
    except Exception as err:
        # if not successful, print and catch the error
        print(err)
        return "internal server error", 500

    # if the file put/update was successful, we need to put a message onto our queue
    # create the message with these key-value pairs
    message = {
        # convert fid obj into a str
        "video_fid": str(fid),
        # for now it's None, but it will be changed later in the downstream
        "mp3_fid": None,
        # username to identify who owns the file, access comes from our auth svc
        "username": access["username"],
    }

    # try and put the message on the queue
    try:
        # use channel (rabbitmq) that's passed into the upload function
        # our rabbitmq by default dispatches messages to our consuming services using the round robin algorithm,
        # which means that the messages will be distributed evenly amongst our consumers
        channel.basic_publish(
            # empty string means default exchange (rabbitmq), which means we set our routing key to the name of the queue
            # that we want our message to be directed to, and set the exchange to the default exchange
            # and that will result to our exchange going to the route specified by our routing key
            exchange="",
            routing_key="video",
            # json.dumps converts the obj to a json formatted str
            body=json.dumps(message),
            # very important to make sure our messages are persisted in our code
            # in the event of a pod crash or a restart of our pod
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
        )
    except Exception as err:
        print(err)
        # if there's no message on the queue (message unsuccessfully added to the queue),
        # but file exists in the db it won't ever get processed,
        # so we need to delete it here if we get an exception/error
        fs.delete(fid)
        return "internal server error", 500
