import os
import re
import hashlib
import datetime
import binascii
import traceback
import functools

import jwt
from flask import Flask, Response, request, send_from_directory

import conf
import dbutil
from errors import Error, InternalError


app = Flask(__name__, static_folder=conf.FRONTEND_DIR)


def guarded(viewfunc):
    @functools.wraps(viewfunc)
    def wrapped(*args, **kwargs):
        try:
            resp = viewfunc(*args, **kwargs)
            return resp
        except Error as e:
            return e.resp
        except Exception:
            traceback.print_exc()
            return InternalError().resp
    return wrapped


@app.route('/api/register', methods=['POST'])
@guarded
def register():
    return do_register(*get_username_and_password())


@app.route('/api/login', methods=['POST'])
@guarded
def login():
    return do_login(*get_username_and_password())


@app.route('/get-register')
@guarded
def get_register():
    return do_register(*get_username_and_password(request.args))


@app.route('/get-login')
@guarded
def get_login():
    return do_login(*get_username_and_password(request.args))


@app.route('/')
@app.route('/<path:path>')
def index(path=''):
    fpath = os.path.abspath(os.path.join(conf.FRONTEND_DIR, path))
    if os.path.isfile(fpath):
        return send_from_directory(conf.FRONTEND_DIR, path)
    return app.send_static_file('index.html')


@app.after_request
def after_request(r):
    if conf.debugging:
        r.headers['Cache-Control'] = 'no-cache'
    r.headers['Access-Control-Allow-Origin'] = request.headers.get('origin', '*')
    r.headers['Access-Control-Allow-Headers'] = 'content-type'
    return r


def do_login(username, password):
    validate_username(username)
    validate_password(password)
    user = dbutil.get_user(username)
    if not user:
        raise Error('not found', 404)

    if hash_password(password, user['salt']) != user['hashed_password']:
        raise Error('wrong password')
    return token_response(dbutil.get_user_for_token(username))


def do_register(username, password):
    validate_username(username)
    validate_password(password)

    if dbutil.get_user(username):
        raise Error('user already exists')

    salt = generate_salt()
    hashed_password = hash_password(password, salt)
    user = {
        'username': username,
        'ctime': utc_now_as_str(),
        'salt': salt,
        'hashed_password': hashed_password,
    }
    if not dbutil.create_user(user):
        raise InternalError()

    return token_response(dbutil.get_user_for_token(username))


def get_username_and_password(data=None):
    if data is None:
        data = request.json
    if not data:
        raise Error('username and password required')
    username = get_string_field('username', data)
    password = get_string_field('password', data)
    return username, password


def get_string_field(name, data):
    value = data.get(name)
    if value is None:
        raise Error(name + ' required', 400)
    if not isinstance(value, (str, unicode)):
        raise Error('invalid ' + name, 400)
    return value


def validate_username(username):
    if not username:
        raise Error('username can not be empty')
    if len(username) > conf.max_username_length:
        raise Error('username too long, should be less than {}'.format(
            conf.max_username_length))
    if not re.match('[-0-9a-z]+', username):
        raise Error('username can only contain '
                    + 'lowercase letters, digits and dash')


def validate_password(password):
    if not password:
        raise Error('password can not be empty')
    if len(password) > conf.max_password_length:
        raise Error('password too long, should be less than {}'.format(
            conf.max_password_length))


def token_response(data):
    token = make_token(data)
    resp = Response(token)
    resp.headers['Content-Type'] = 'application/json'
    if 'no-cookie' not in request.args:
        date = datetime.datetime.now() + datetime.timedelta(days=90)
        resp.set_cookie('token', token, expires=date)
    return resp


def make_token(data):
    return jwt.encode(data, conf.prikey, algorithm='RS512')


def generate_salt():
    return binascii.hexlify(os.urandom(32))


def hash_password(password, salt, iterations=100000):
    hashed_pwd = hashlib.pbkdf2_hmac('sha256', password, salt, iterations)
    return binascii.hexlify(hashed_pwd)


def utc_now_as_str():
    return datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')


if __name__ == '__main__':
    app.run(
        host=conf.host,
        port=conf.port,
        threaded=True,
        debug=conf.debugging,
    )
