from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ---------------------- User Model ----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    profile_picture = db.Column(db.String(255), default='default.png')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship: A user can follow many users
    following = db.relationship(
        'Follow',
        foreign_keys='Follow.follower_id',
        backref='follower',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def is_following(self, user):
        return Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first() is not None

    # Retrieve all followed users
    def get_followed_users(self):
        return [follow.followed for follow in self.following]

# ---------------------- Follow Model ----------------------
class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationship to get the followed user
    followed = db.relationship("User", foreign_keys=[followed_id])

# ---------------------- Post Model ----------------------
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('posts', lazy=True))

    # Relationship to Likes (Fixing the conflict)
    likes = db.relationship('Like', backref='post', lazy=True, cascade="all, delete-orphan")

    def total_likes(self):
        return len(self.likes)

# ---------------------- Comment Model ----------------------
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('comments', lazy=True))

# ---------------------- Likes Model ----------------------
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('likes', lazy=True))
