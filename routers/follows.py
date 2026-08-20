from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Follow, User


router = APIRouter(
    prefix="/users",
    tags=["Follows"]
)


# ============================================================
# FOLLOW USER
# ============================================================

@router.post(
    "/{username}/follow",
    status_code=status.HTTP_201_CREATED
)
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_to_follow = db.query(User).filter(
        User.username == username
    ).first()

    if not user_to_follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent following yourself
    if user_to_follow.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot follow yourself"
        )

    # Prevent duplicate follows
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_to_follow.id
    ).first()

    if existing_follow:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already follow this user"
        )

    follow = Follow(
        follower_id=current_user.id,
        following_id=user_to_follow.id
    )

    db.add(follow)
    db.commit()
    db.refresh(follow)

    return {
        "message": "User followed successfully",
        "username": user_to_follow.username
    }


# ============================================================
# UNFOLLOW USER
# ============================================================

@router.delete(
    "/{username}/follow"
)
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_to_unfollow = db.query(User).filter(
        User.username == username
    ).first()

    if not user_to_unfollow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_to_unfollow.id
    ).first()

    if not follow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not following this user"
        )

    db.delete(follow)
    db.commit()

    return {
        "message": "User unfollowed successfully",
        "username": user_to_unfollow.username
    }


# ============================================================
# GET FOLLOWERS
# ============================================================

@router.get(
    "/{username}/followers"
)
def get_followers(
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

    results = (
        db.query(User)
        .join(
            Follow,
            Follow.follower_id == User.id
        )
        .filter(
            Follow.following_id == user.id
        )
        .order_by(
            Follow.created_at.desc()
        )
        .all()
    )

    return {
        "username": user.username,
        "followers_count": len(results),
        "followers": [
            {
                "id": follower.id,
                "username": follower.username
            }
            for follower in results
        ]
    }


# ============================================================
# GET FOLLOWING
# ============================================================

@router.get(
    "/{username}/following"
)
def get_following(
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

    results = (
        db.query(User)
        .join(
            Follow,
            Follow.following_id == User.id
        )
        .filter(
            Follow.follower_id == user.id
        )
        .order_by(
            Follow.created_at.desc()
        )
        .all()
    )

    return {
        "username": user.username,
        "following_count": len(results),
        "following": [
            {
                "id": followed_user.id,
                "username": followed_user.username
            }
            for followed_user in results
        ]
    }