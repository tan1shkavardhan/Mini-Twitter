from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query
)

from sqlalchemy import (
    and_,
    exists,
    func
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user

from app.models import (
    Comment,
    Hashtag,
    Like,
    Repost,
    Tweet,
    User
)

from app.schemas import TweetListResponse

from routers.tweets import (
    build_tweet_response
)


router = APIRouter(
    prefix="/hashtags",
    tags=["Hashtags"]
)


# ============================================================
# GET TWEETS BY HASHTAG
# ============================================================

@router.get(
    "/{name}/tweets",
    response_model=TweetListResponse
)
def get_tweets_by_hashtag(
    name: str,
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

    normalized_name = name.strip().lower()

    hashtag = (
        db.query(Hashtag)
        .filter(
            Hashtag.name == normalized_name
        )
        .first()
    )

    if not hashtag:
        raise HTTPException(
            status_code=404,
            detail="Hashtag not found"
        )

    like_count_subquery = (
        db.query(
            Like.tweet_id,
            func.count(Like.id).label(
                "like_count"
            )
        )
        .group_by(
            Like.tweet_id
        )
        .subquery()
    )

    comment_count_subquery = (
        db.query(
            Comment.tweet_id,
            func.count(Comment.id).label(
                "comment_count"
            )
        )
        .group_by(
            Comment.tweet_id
        )
        .subquery()
    )

    repost_count_subquery = (
        db.query(
            Repost.tweet_id,
            func.count(Repost.id).label(
                "repost_count"
            )
        )
        .group_by(
            Repost.tweet_id
        )
        .subquery()
    )

    liked_by_me_subquery = exists().where(
        and_(
            Like.tweet_id == Tweet.id,
            Like.user_id == current_user.id
        )
    )

    reposted_by_me_subquery = exists().where(
        and_(
            Repost.tweet_id == Tweet.id,
            Repost.user_id == current_user.id
        )
    )

    query = (
        db.query(
            Tweet,
            User.username,

            func.coalesce(
                like_count_subquery.c.like_count,
                0
            ).label("like_count"),

            func.coalesce(
                comment_count_subquery.c.comment_count,
                0
            ).label("comment_count"),

            func.coalesce(
                repost_count_subquery.c.repost_count,
                0
            ).label("repost_count"),

            liked_by_me_subquery.label(
                "liked_by_me"
            ),

            reposted_by_me_subquery.label(
                "reposted_by_me"
            )
        )
        .join(
            User,
            Tweet.user_id == User.id
        )
        .join(
            Tweet.hashtags
        )
        .filter(
            Hashtag.id == hashtag.id
        )
        .outerjoin(
            like_count_subquery,
            like_count_subquery.c.tweet_id == Tweet.id
        )
        .outerjoin(
            comment_count_subquery,
            comment_count_subquery.c.tweet_id == Tweet.id
        )
        .outerjoin(
            repost_count_subquery,
            repost_count_subquery.c.tweet_id == Tweet.id
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

    tweets = [
        build_tweet_response(
            tweet=tweet,
            username=username,
            like_count=like_count,
            liked_by_me=bool(liked_by_me),
            comment_count=comment_count,
            repost_count=repost_count,
            reposted_by_me=bool(reposted_by_me)
        )
        for (
            tweet,
            username,
            like_count,
            comment_count,
            repost_count,
            liked_by_me,
            reposted_by_me
        ) in results
    ]

    return TweetListResponse(
        tweets=tweets,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total
    )