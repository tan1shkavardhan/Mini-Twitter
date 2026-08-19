from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

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
        nullable=False
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
        default=lambda: datetime.now(timezone.utc)
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


class Like(Base):
    __tablename__ = "likes"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "tweet_id",
            name ="unique_user_tweet_like"
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
        nullable=False
    )

    tweet_id = Column(
        Integer,
        ForeignKey("tweets.id"),
        nullable=False
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