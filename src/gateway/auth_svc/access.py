# this file is a package because of __init__.py in this directory
import os
import requests


def login(request):
    # note: 'request' (parameter) is different from 'requests' (imported)
    auth = request.authorization
    if not auth:
        return None, ("missing credentials", 401)

    basicAuth = (auth.username, auth.password)

    # 'requests' is what is going to make the http/api call (post request) to our auth service
    # once this request completes, this response is going to contain the result
    response = requests.post(
        f"http://{os.environ.get('AUTH_SVC_ADDRESS')}/login",
        auth=basicAuth
    )

    if response.status_code == 200:
        return response.text, None
    else:
        return None, (response.text, response.status_code)
