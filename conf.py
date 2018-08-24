import os


debugging = os.path.exists('DEBUG')


host = '0.0.0.0'
port = 6561

user_dir = os.path.expanduser('~')
ssh_dir = os.path.join(user_dir, '.ssh')

with open(os.path.join(ssh_dir, 'id_rsa')) as f:
    prikey = f.read().strip()

with open(os.path.join(ssh_dir, 'id_rsa.pub')) as f:
    pubkey = f.read().strip()

max_username_length = 16
max_password_length = 64
