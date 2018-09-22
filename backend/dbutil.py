import db


def create_user(user):
    user = dict(user)
    user.update({'_id': user['username']})
    r = db.getdb().user.insert_one(user)
    return r.acknowledged


def get_user_for_token(username):
    user = get_user(username)
    if not user:
        return None
    return {
        'username': user['username'],
    }


def get_user(username):
    return db.getdb().user.find_one({
        'username': username,
    })


def remove_user(username):
    r = db.getdb().user.remove({'username': username})
    return r['n'] == 1
