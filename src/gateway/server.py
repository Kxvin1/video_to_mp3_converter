import os
import gridfs
import pika
import json
from flask import Flask, request
from flask_pymongo import PyMongo
from auth import validate
from auth_svc import access
from storage import util

server = Flask(__name__)

# our mongo URI is on mongodb and the name of the database will be videos. 27017 is the default mongodb port
server.config["MONGO_URI"] = "mongodb://host.minikube.internal:27017/videos"

# start the mongo db server
mongo = PyMongo(server)

# gridFS future roofs our app by allowing us to work with files larger than 16mb
fs = gridfs.GridFS(mongo.db)

# make our communication with RabbitMQ synchronous
connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()


# login route
@server.route("/login", methods=["POST"])
def login():
    # the request is from flask and we're importing it above
    # 'access' is a package we created and imported (located in ./auth_svc/access.py) -- the return is a tuple
    token, err = access.login(request)

    if not err:
        return token
    else:
        return err


# upload route/end point
@server.route("/upload", methods=["POST"])
def upload():
    # 'validate' is a package we created and imported (located in ./auth/validate.py) -- the return is a tuple
    # access will resolve to 'response.text' that contains that JSON string that contains our payload with our claims
    access, err = validate.token(request)

    # json.loads convert this access json string to a python object (so we can work with it)
    access = json.loads(access)

    if access["admin"]:
        # we only want 1 file from the request.files dictionary
        if len(request.files) > 1 or len(request.files) < 1:
            return "exactly 1 file required", 400

        for key, f in request.files.items():
            # 'util' is a package we created and imported (located in ./storage/util.py) -- the return is None or an error
            # upload takes 4 params: our file 'f', gridfs 'fs' for increased size (scale), rabbitmq channel 'channel', and access 'access'
            # it will return an err if there is something wrong, otherwise it will return None
            err = util.upload(f, fs, channel, access)

            if err:
                return err

        return "success", 200
    else:
        return "not authorized", 401


# download end point/route
@server.route("/download", methods=["GET"])
def download():
    pass


# The if __name__ == "__main__": block is often used to specify code that should only be run when the module is
# executed as a script, rather than imported as a module. This allows you to use the same module in multiple
# places without running the code in the if block every time the module is imported.
if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)
