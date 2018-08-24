import os
import re
import hashlib
import datetime
import binascii
import traceback
import functools

import jwt
import flask

import conf
import dbutil
from errors import Error, InternalError


app = flask.Flask(__name__)


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


@app.route('/register', methods=['POST'])
@guarded
def register():
    username, password = get_username_and_password()
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


@app.route('/login', methods=['POST'])
@guarded
def login():
    username, password = get_username_and_password()
    validate_username(username)
    validate_password(password)

    user = dbutil.get_user(username)
    if not user:
        raise Error('not found', 404)

    if hash_password(password, user['salt']) != user['hashed_password']:
        raise Error('wrong password')
    return token_response(dbutil.get_user_for_token(username))


@app.after_request
def after_request(r):
    if conf.debugging:
        r.headers['Cache-Control'] = 'no-cache'
    return r


def get_username_and_password():
    data = flask.request.json
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
    resp = flask.Response(token)
    if 'no-cookie' not in flask.request.args:
        resp.set_cookie('token', token)
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
