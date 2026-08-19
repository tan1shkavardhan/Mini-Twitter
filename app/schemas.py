from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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

class TweetListResponse(BaseModel):
    tweets: list[TweetResponse]
    page: int
    limit: int
    total: int
    has_next: bool
   
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str

#profile
class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    tweet_count: int

class UserTweetsResponse(BaseModel):
    username: str
    tweets: list[TweetResponse]
    page: int
    limit: int
    total: int
    has_next: bool