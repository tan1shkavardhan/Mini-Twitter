from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Follow, Tweet, User
from app.schemas import TweetListResponse
from routers.tweets import (
    get_tweet_query,
    make_tweet_response
)


router = APIRouter(
    prefix="/feed",
    tags=["Feed"]
)


@router.get(
    "/",
    response_model=TweetListResponse
)
def get_feed(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    following_ids = (
        db.query(Follow.following_id)
        .filter(
            Follow.follower_id == current_user.id
        )
    )

    query = (
        get_tweet_query(
            db,
            current_user.id
        )
        .filter(
            Tweet.user_id.in_(following_ids)
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

    return TweetListResponse(
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total
    )