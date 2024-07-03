from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, email, password,role='user', _id=None):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role  # Default role is user
        self._id=_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_username_or_email(cls, mongo, username, email):
        user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        return user
    
    @classmethod
    def get_by_username(cls, mongo, username):
        user = mongo.db.users.find_one({'username': username})
        return user

    @classmethod
    def get_by_id(cls, mongo, user_id):
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return user
    
    
    def get_id(self):
        # Ensure the `_id` is converted to string to prevent serialization issues.
        return str(self._id) if self._id else None
    
    @classmethod
    def get_all_users(cls, mongo):
        users = mongo.db.users.find({'role': 'user'})
        admins= mongo.db.users.find({'role': 'admin'})
        return users
    
    @classmethod
    def get_all_admins(cls, mongo):
        admins= mongo.db.users.find({'role': 'admin'})
        return admins


    def save(self, mongo):
        user_id = mongo.db.users.insert_one({
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role
        }).inserted_id
        self.id = user_id
        return self

class Admin(UserMixin):
    def __init__(self, username, email, password, _id=None,role='admin'):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.role = role
        self._id=_id

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_username_or_email(cls, mongo, username, email):
        user = mongo.db.users.find_one({'$or': [{'username': username}, {'email': email}]})
        return user
    
    @classmethod
    def get_by_username(cls, mongo, username):
        user = mongo.db.users.find_one({'username': username})
        return user

    @classmethod
    def get_by_id(cls, mongo, user_id):
        user = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return user
    
    
    def get_id(self):
        # Ensure the `_id` is converted to string to prevent serialization issues.
        return str(self._id) if self._id else None

    def save(self, mongo):
        user_id = mongo.db.users.insert_one({
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'role': self.role
        }).inserted_id
        self.id = user_id
        return self
