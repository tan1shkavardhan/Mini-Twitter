from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Like, Tweet, User
from app.schemas import (
    TweetResponse,
    UserProfileResponse,
    UserTweetsResponse
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


def build_user_tweet_response(
    tweet: Tweet,
    username: str,
    like_count: int,
    liked_by_me: bool
) -> TweetResponse:
    return TweetResponse(
        id=tweet.id,
        user_id=tweet.user_id,
        username=username,
        text=tweet.text,
        photo=tweet.photo,
        created_at=tweet.created_at,
        updated_at=tweet.updated_at,
        like_count=like_count,
        liked_by_me=liked_by_me
    )


# ============================================================
# GET USER PROFILE
# ============================================================

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


# ============================================================
# GET USER'S TWEETS
# ============================================================

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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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
        .filter(
            Tweet.user_id == user.id
        )
        .order_by(
            Tweet.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    tweet_data = []

    for tweet in tweets:

        like_count = db.query(Like).filter(
            Like.tweet_id == tweet.id
        ).count()

        liked_by_me = db.query(Like).filter(
            Like.tweet_id == tweet.id,
            Like.user_id == current_user.id
        ).first() is not None

        tweet_data.append(
            build_user_tweet_response(
                tweet=tweet,
                username=user.username,
                like_count=like_count,
                liked_by_me=liked_by_me
            )
        )

    has_next = (page * limit) < total

    return UserTweetsResponse(
        username=user.username,
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=has_next
    )