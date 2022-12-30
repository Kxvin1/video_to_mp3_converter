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
