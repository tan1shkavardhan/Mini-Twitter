from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Bookmark, Tweet, User
from sqlalchemy import and_, exists, func
from app.models import Comment, Like
from app.schemas import TweetListResponse
from routers.tweets import build_tweet_response

router = APIRouter(
    prefix="/tweets",
    tags=["Bookmarks"]
)


# ============================================================
# BOOKMARK TWEET
# ============================================================

@router.post(
    "/{tweet_id}/bookmark",
    status_code=status.HTTP_201_CREATED
)
def bookmark_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tweet = db.query(Tweet).filter(
        Tweet.id == tweet_id
    ).first()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

    existing_bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.tweet_id == tweet_id
    ).first()

    if existing_bookmark:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tweet already bookmarked"
        )

    bookmark = Bookmark(
        user_id=current_user.id,
        tweet_id=tweet_id
    )

    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)

    return {
        "message": "Tweet bookmarked successfully",
        "tweet_id": tweet_id
    }


# ============================================================
# REMOVE BOOKMARK
# ============================================================

@router.delete(
    "/{tweet_id}/bookmark"
)
def remove_bookmark(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.tweet_id == tweet_id
    ).first()

    if not bookmark:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookmark not found"
        )

    db.delete(bookmark)
    db.commit()

    return {
        "message": "Bookmark removed successfully",
        "tweet_id": tweet_id
    }

# ============================================================
# GET MY BOOKMARKS
# ============================================================

@router.get(
    "/me/bookmarks",
    response_model=TweetListResponse
)
def get_my_bookmarks(
    page: int = 1,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    results = (
        db.query(Tweet, User.username)
        .join(Bookmark, Bookmark.tweet_id == Tweet.id)
        .join(User, Tweet.user_id == User.id)
        .filter(Bookmark.user_id == current_user.id)
        .order_by(Bookmark.created_at.desc())
        .all()
    )

    tweets = [
        build_tweet_response(
            tweet=tweet,
            username=username,
            like_count=len(tweet.likes),
            liked_by_me=any(
                like.user_id == current_user.id
                for like in tweet.likes
            ),
            comment_count=len(tweet.comments)
        )
        for tweet, username in results
    ]

    total = len(tweets)

    start = (page - 1) * limit
    end = start + limit

    return TweetListResponse(
        tweets=tweets[start:end],
        page=page,
        limit=limit,
        total=total,
        has_next=end < total
    )