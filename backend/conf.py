import os


debugging = os.path.exists('DEBUG')



host = os.environ.get('HOST') or '0.0.0.0'
port = int(os.environ.get('PORT', 4433))

user_dir = os.path.expanduser('~')
ssh_dir = os.path.join(user_dir, '.ssh')

with open(os.path.join(ssh_dir, 'id_rsa')) as f:
    prikey = f.read().strip()

with open(os.path.join(ssh_dir, 'id_rsa.pub')) as f:
    pubkey = f.read().strip()

max_username_length = 16
max_password_length = 64


FRONTEND_DIR = os.path.abspath('../frontend/build/')
