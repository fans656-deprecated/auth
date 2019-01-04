#!/usr/bin/env python3
import getpass

import requests
from flask import *


res = requests.post('https://auth.fans656.me/api/login', json={
    'username': 'fans656',
    'password': getpass.getpass('Enter the password: '),
}, proxies={'https': '192.168.56.1:1080'})
if res.status_code != 200:
    print('ERROR - Failed to fetch token')
    print(res.text)
    exit(1)
token = res.text


app = Flask(__name__)


@app.route('/')
def index():
    return token


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9999, threaded=True)
