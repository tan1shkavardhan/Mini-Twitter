from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Repost, Tweet, User
from app.notification_utils import create_notification


router = APIRouter(
    prefix="/tweets",
    tags=["Reposts"]
)


# ============================================================
# REPOST TWEET
# ============================================================

@router.post(
    "/{tweet_id}/repost",
    status_code=status.HTTP_201_CREATED
)
def repost_tweet(
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

    existing_repost = db.query(Repost).filter(
        Repost.user_id == current_user.id,
        Repost.tweet_id == tweet_id
    ).first()

    if existing_repost:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already reposted this tweet"
        )

    repost = Repost(
        user_id=current_user.id,
        tweet_id=tweet_id
    )

    db.add(repost)

    create_notification(
        db=db,
        user_id=tweet.user_id,
        actor_id=current_user.id,
        notification_type="repost",
        tweet_id=tweet.id,
    )

    db.commit()
    db.refresh(repost)

    return {
        "message": "Tweet reposted successfully",
        "tweet_id": tweet_id,
        "repost_id": repost.id
    }


# ============================================================
# REMOVE REPOST
# ============================================================

@router.delete(
    "/{tweet_id}/repost"
)
def remove_repost(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repost = db.query(Repost).filter(
        Repost.user_id == current_user.id,
        Repost.tweet_id == tweet_id
    ).first()

    if not repost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You have not reposted this tweet"
        )

    db.delete(repost)
    db.commit()

    return {
        "message": "Repost removed successfully",
        "tweet_id": tweet_id
    }


# ============================================================
# GET REPOST COUNT
# ============================================================

@router.get(
    "/{tweet_id}/reposts"
)
def get_repost_count(
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

    repost_count = db.query(Repost).filter(
        Repost.tweet_id == tweet_id
    ).count()

    return {
        "tweet_id": tweet_id,
        "repost_count": repost_count
    }