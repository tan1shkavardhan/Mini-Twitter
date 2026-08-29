from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Table
)

from sqlalchemy.orm import relationship

from .database import Base


# ============================================================
# USER
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    email = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    tweets = relationship(
        "Tweet",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    likes = relationship(
        "Like",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    bookmarks = relationship(
        "Bookmark",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    comments = relationship(
        "Comment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    reposts = relationship(
        "Repost",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Users this user follows
    following = relationship(
        "Follow",
        foreign_keys="Follow.follower_id",
        back_populates="follower",
        cascade="all, delete-orphan"
    )

    # Users following this user
    followers = relationship(
        "Follow",
        foreign_keys="Follow.following_id",
        back_populates="following",
        cascade="all, delete-orphan"
    )

    notifications = relationship(
        "Notification",
        foreign_keys="Notification.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    sent_notifications = relationship(
        "Notification",
        foreign_keys="Notification.actor_id",
        back_populates="actor"
    )


# ============================================================
# TWEET HASHTAGS (MANY-TO-MANY)
# ============================================================

tweet_hashtags = Table(
    "tweet_hashtags",
    Base.metadata,

    Column(
        "tweet_id",
        Integer,
        ForeignKey("tweets.id"),
        primary_key=True
    ),

    Column(
        "hashtag_id",
        Integer,
        ForeignKey("hashtags.id"),
        primary_key=True
    ),
)


# ============================================================
# TWEET
# ============================================================

class Tweet(Base):
    __tablename__ = "tweets"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    text = Column(
        Text,
        nullable=False
    )

    photo = Column(
        String(255),
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        back_populates="tweets"
    )

    likes = relationship(
        "Like",
        back_populates="tweet",
        cascade="all, delete-orphan"
    )

    bookmarks = relationship(
        "Bookmark",
        back_populates="tweet",
        cascade="all, delete-orphan"
    )

    comments = relationship(
        "Comment",
        back_populates="tweet",
        cascade="all, delete-orphan"
    )

    hashtags = relationship(
        "Hashtag",
        secondary=tweet_hashtags,
        back_populates="tweets"
    )

    reposts = relationship(
        "Repost",
        back_populates="tweet",
        cascade="all, delete-orphan"
    )

# ============================================================
# HASHTAG
# ============================================================

class Hashtag(Base):
    __tablename__ = "hashtags"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    tweets = relationship(
        "Tweet",
        secondary=tweet_hashtags,
        back_populates="hashtags"
    )

# ============================================================
# LIKE
# ============================================================

class Like(Base):
    __tablename__ = "likes"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tweet_id",
            name="unique_user_tweet_like"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        back_populates="likes"
    )

    tweet = relationship(
        "Tweet",
        back_populates="likes"
    )

# ============================================================
# BOOKMARK
# ============================================================

class Bookmark(Base):
    __tablename__ = "bookmarks"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tweet_id",
            name="unique_user_tweet_bookmark"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        back_populates="bookmarks"
    )

    tweet = relationship(
        "Tweet",
        back_populates="bookmarks"
    )


# ============================================================
# COMMENT
# ============================================================

class Comment(Base):
    __tablename__ = "comments"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id"),
        nullable=False,
        index=True
    )

    # NULL = direct comment on tweet
    # ID = reply to another comment
    parent_comment_id = Column(
        Integer,
        ForeignKey("comments.id"),
        nullable=True,
        index=True
    )

    text = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        back_populates="comments"
    )

    tweet = relationship(
        "Tweet",
        back_populates="comments"
    )

    # Parent comment, if this is a reply
    parent = relationship(
        "Comment",
        remote_side=[id],
        back_populates="replies"
    )

    # Replies to this comment
    replies = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan"
    )


# ============================================================
# FOLLOW
# ============================================================

class Follow(Base):
    __tablename__ = "follows"

    __table_args__ = (
        UniqueConstraint(
            "follower_id",
            "following_id",
            name="unique_follower_following"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    follower_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    following_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    follower = relationship(
        "User",
        foreign_keys=[follower_id],
        back_populates="following"
    )

    following = relationship(
        "User",
        foreign_keys=[following_id],
        back_populates="followers"
    )


# ============================================================
# NOTIFICATION
# ============================================================

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # Person receiving the notification
    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Person who caused the notification
    actor_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # like / follow / comment / reply
    type = Column(
        String(50),
        nullable=False
    )

    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id"),
        nullable=True,
        index=True
    )

    comment_id = Column(
        Integer,
        ForeignKey("comments.id"),
        nullable=True,
        index=True
    )

    is_read = Column(
        Integer,
        default=0,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        index=True
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="notifications"
    )

    actor = relationship(
        "User",
        foreign_keys=[actor_id],
        back_populates="sent_notifications"
    )

    tweet = relationship(
        "Tweet"
    )

    comment = relationship(
        "Comment"
    )

# ============================================================
# REPOST
# ============================================================

class Repost(Base):
    __tablename__ = "reposts"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tweet_id",
            name="unique_user_tweet_repost"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id"),
        nullable=False,
        index=True
    )

    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    user = relationship(
        "User",
        back_populates="reposts"
    )

    tweet = relationship(
        "Tweet",
        back_populates="reposts"
    )