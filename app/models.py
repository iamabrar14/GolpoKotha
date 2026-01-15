from datetime import datetime
from flask_login import UserMixin
from . import db, bcrypt

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), primary_key=True),
    db.Column('timestamp', db.DateTime, default=datetime.utcnow)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # Case-insensitive unique usernames via SQLite NOCASE collation
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    bio = db.Column(db.Text, nullable=True, default='')  # Added bio field

    posts = db.relationship('Post', backref='author', cascade='all, delete-orphan', passive_deletes=True)
    comments = db.relationship('Comment', backref='commenter', cascade='all, delete-orphan', passive_deletes=True)
    
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )
    
    notifications = db.relationship('Notification', foreign_keys='Notification.user_id', backref='recipient', cascade='all, delete-orphan', passive_deletes=True)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followers_count(self):
        return self.followers.count()

    def following_count(self):
        return self.followed.count()

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(
            followers.c.follower_id == self.id
        ).order_by(Post.date_posted.desc())
    
    def unread_notifications_count(self):
        """Returns count of unread notifications for this user."""
        return Notification.query.filter_by(user_id=self.id, is_read=False).count()
    
    def get_notifications(self, limit=None, unread_only=False):
        """Returns user's notifications, optionally filtered and limited."""
        query = Notification.query.filter_by(user_id=self.id)
        if unread_only:
            query = query.filter_by(is_read=False)
        query = query.order_by(Notification.created_at.desc())
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def mark_notifications_read(self):
        """Marks all notifications as read for this user."""
        Notification.query.filter_by(user_id=self.id, is_read=False).update({'is_read': True})
        db.session.commit()


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    category = db.Column(db.String(30), nullable=False, default="Others")


    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)

    comments = db.relationship('Comment', backref='post', cascade='all, delete, delete-orphan', passive_deletes=True)
    likes = db.Column(db.Integer, default=0) 
    views = db.Column(db.Integer, default=0) 

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    date_commented = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id', ondelete='CASCADE'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='_user_post_like_uc'),)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    notification_type = db.Column(db.String(20), nullable=False)  # 'like', 'comment', 'follow', 'new_post'
    message = db.Column(db.String(255), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_notifications')
    
    @staticmethod
    def create_notification(user_id, sender_id, notification_type, message, link=None):
        """Create a new notification."""
        notification = Notification(
            user_id=user_id,
            sender_id=sender_id,
            notification_type=notification_type,
            message=message,
            link=link
        )
        db.session.add(notification)
        db.session.commit()
        return notification