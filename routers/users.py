from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Follow, Tweet, User
from app.schemas import (
    UserProfileResponse,
    UserTweetsResponse
)

from routers.tweets import (
    get_tweet_query,
    make_tweet_response
)


router = APIRouter(
    prefix="/users",
    tags=["Users"]
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

    tweet_count = db.query(Tweet).filter(
        Tweet.user_id == user.id
    ).count()

    followers_count = db.query(Follow).filter(
        Follow.following_id == user.id
    ).count()

    following_count = db.query(Follow).filter(
        Follow.follower_id == user.id
    ).count()

    following = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user.id
    ).first() is not None

    return UserProfileResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        created_at=user.created_at,
        tweet_count=tweet_count,
        followers_count=followers_count,
        following_count=following_count,
        following=following
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

    query = (
        get_tweet_query(
            db,
            current_user.id
        )
        .filter(
            Tweet.user_id == user.id
        )
    )

    total = query.count()

    offset = (page - 1) * limit

    results = (
        query
        .order_by(
            Tweet.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    tweet_data = [
        make_tweet_response(result)
        for result in results
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