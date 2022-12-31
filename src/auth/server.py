import jwt
import datetime
import os
from flask import Flask, request
from flask_mysqldb import MySQL

server = Flask(__name__)
mysql = MySQL(server)

# config
server.config["MYSQL_HOST"] = os.environ.get("MYSQL_HOST")
server.config["MYSQL_USER"] = os.environ.get("MYSQL_USER")
server.config["MYSQL_PASSWORD"] = os.environ.get("MYSQL_PASSWORD")
server.config["MYSQL_DB"] = os.environ.get("MYSQL_DB")
server.config["MYSQL_PORT"] = os.environ.get("MYSQL_PORT")
# print(server.config["MYSQL_HOST"])


# login route
@server.route("/login", methods=["POST"])
def login():
    auth = request.authorization
    if not auth:
        return "missing credentials", 401

    # check db for username and password
    cur = mysql.connection.cursor()
    res = cur.execute(
        "SELECT email, password FROM user WHERE email=%s", (auth.username,)
    )

    if res > 0:
        user_row = cur.fetchone()
        email = user_row[0]
        password = user_row[1]

        if auth.username != email or auth.password != password:
            return "invalid credentials", 401
        else:
            return createJWT(auth.username, os.environ.get("JWT_SECRET"), True)
    else:
        return "invalide credentials", 401


# creates JWT token
def createJWT(username, secret, authz):
    # these are our 'claims'
    return jwt.encode(
        {
            "username": username,
            # set expiration to 1 day
            "exp": datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(days=1),
            # when token is issued
            "iat": datetime.datetime.utcnow(),
            # whether the user has admin privs
            "admin": authz,
        },
        secret,
        algorithm="HS256",
    )


# route used by api gateway to validate jwts sent within requests from the client,
# to both upload and receive, or download mp3s/videos
@server.route("/validate", methods=["POST"])
def validate():
    encoded_jwt = request.headers["Authorization"]

    if not encoded_jwt:
        return "missing credentials", 401

    # Bearer <Token> -- this gives back the token
    encoded_jwt = encoded_jwt.split(" ")[1]

    try:
        decoded = jwt.decode(
            encoded_jwt, os.environ.get("JWT_SECRET"), algorithm=["HS256"]
        )
    except:
        return "not authorized", 403

    return decoded, 200


# what this means: when we run this file, using the python command, then this name variable will result to main
if __name__ == "__main__":
    # print(__name__) --> __name__

    # default host is localhost, but we want an externally visible server, this tells our operating system to listen on all public IPs
    # otherwise, the server is only accessible on our local
    # so when we set host to 0.0.0.0, we are telling our flask app to listen on all of our docker containers ips, including the loopback (localhost) or any other ip address on the docker container
    # this is so it can listen to any docker container, which each have their own ip address
    server.run(host="0.0.0.0", port=5000)
