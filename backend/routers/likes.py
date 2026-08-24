from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Like, Tweet, User


router = APIRouter(
    prefix="/tweets",
    tags=["Likes"]
)


@router.post(
    "/{tweet_id}/like",
    status_code=status.HTTP_201_CREATED
)
def like_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Check that tweet exists
    tweet = db.query(Tweet).filter(
        Tweet.id == tweet_id
    ).first()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

    # Check whether user already liked it
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.tweet_id == tweet_id
    ).first()

    if existing_like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already liked this tweet"
        )

    like = Like(
        user_id=current_user.id,
        tweet_id=tweet_id
    )

    db.add(like)
    db.commit()
    db.refresh(like)

    return {
        "message": "Tweet liked successfully",
        "tweet_id": tweet_id,
        "like_id": like.id
    }


@router.delete(
    "/{tweet_id}/like"
)
def unlike_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.tweet_id == tweet_id
    ).first()

    if not like:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not liked this tweet"
        )

    db.delete(like)
    db.commit()

    return {
        "message": "Tweet unliked successfully",
        "tweet_id": tweet_id
    }


@router.get(
    "/{tweet_id}/likes"
)
def get_tweet_likes(
    tweet_id: int,
    db: Session = Depends(get_db)
):
    tweet = db.query(Tweet).filter(
        Tweet.id == tweet_id
    ).first()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

    like_count = db.query(Like).filter(
        Like.tweet_id == tweet_id
    ).count()

    return {
        "tweet_id": tweet_id,
        "like_count": like_count
    }