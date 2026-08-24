from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ============================================================
# USER / AUTH
# ============================================================

class UserCreate(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=50
    )
    email: str
    password: str = Field(
        min_length=8,
        max_length=100
    )


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


# ============================================================
# TWEETS
# ============================================================

class TweetCreate(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=280
    )


class TweetResponse(BaseModel):
    id: int
    user_id: int
    username: str
    text: str
    photo: str | None
    created_at: datetime
    updated_at: datetime
    like_count: int
    liked_by_me: bool
    comment_count: int


class TweetListResponse(BaseModel):
    tweets: list[TweetResponse]
    page: int
    limit: int
    total: int
    has_next: bool


# ============================================================
# USER PROFILE
# ============================================================

class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    tweet_count: int
    followers_count: int
    following_count: int
    following: bool


class UserTweetsResponse(BaseModel):
    username: str
    tweets: list[TweetResponse]
    page: int
    limit: int
    total: int
    has_next: bool


# ============================================================
# COMMENTS
# ============================================================

class CommentCreate(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=500
    )


class CommentResponse(BaseModel):
    id: int
    user_id: int
    username: str
    tweet_id: int
    text: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )


class CommentListResponse(BaseModel):
    comments: list[CommentResponse]
    page: int
    limit: int
    total: int
    has_next: bool