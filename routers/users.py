from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Tweet, User
from app.schemas import (
    TweetResponse,
    UserProfileResponse,
    UserTweetsResponse
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get(
    "/{username}",
    response_model=UserProfileResponse
)
def get_user_profile(
    username: str,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    tweet_count = db.query(Tweet).filter(
        Tweet.user_id == user.id
    ).count()

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        tweet_count=tweet_count
    )


@router.get(
    "/{username}/tweets",
    response_model=UserTweetsResponse
)
def get_user_tweets(
    username: str,
    page: int = Query(
        default=1,
        ge=1
    ),
    limit: int = Query(
        default=10,
        ge=1,
        le=50
    ),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == username
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    total = db.query(Tweet).filter(
        Tweet.user_id == user.id
    ).count()

    offset = (page - 1) * limit

    tweets = (
        db.query(Tweet)
        .filter(Tweet.user_id == user.id)
        .order_by(Tweet.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    tweet_data = [
        TweetResponse(
            id=tweet.id,
            user_id=user.id,
            username=user.username,
            text=tweet.text,
            photo=tweet.photo,
            created_at=tweet.created_at,
            updated_at=tweet.updated_at
        )
        for tweet in tweets
    ]

    has_next = (page * limit) < total

    return UserTweetsResponse(
        username=user.username,
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=has_next
    )