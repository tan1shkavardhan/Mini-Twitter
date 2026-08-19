import os
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status
)

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Like, Tweet, User
from app.schemas import (
    TweetCreate,
    TweetListResponse,
    TweetResponse
)


# ============================================================
# CONSTANTS
# ============================================================

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp"
}

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp"
}


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/tweets",
    tags=["Tweets"]
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def save_image(photo: UploadFile) -> str:
    """
    Validate and save an uploaded image.

    Returns:
        str: Path of the saved image.
    """

    # Check Content-Type
    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG and WebP images are allowed"
        )

    # Check file extension
    extension = os.path.splitext(
        photo.filename or ""
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed image extensions: .jpg, .jpeg, .png, .webp"
        )

    # Generate a unique filename
    filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        "uploads",
        filename
    )

    try:
        total_size = 0

        with open(file_path, "wb") as buffer:

            while True:
                # Read 1 MB at a time
                chunk = photo.file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                # Check maximum file size
                if total_size > MAX_IMAGE_SIZE:

                    if os.path.exists(file_path):
                        os.remove(file_path)

                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Image size cannot exceed 5 MB"
                    )

                buffer.write(chunk)

    except HTTPException:
        raise

    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image"
        )

    finally:
        photo.file.close()

    return file_path


def build_tweet_response(
    tweet: Tweet,
    username: str,
    like_count: int,
    liked_by_me: bool
) -> TweetResponse:
    """
    Convert a Tweet database object into our API response.
    """

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


def get_like_info(
    tweet_id: int,
    current_user_id: int,
    db: Session
):
    """
    Get like count and whether the current user liked the tweet.
    """

    like_count = db.query(Like).filter(
        Like.tweet_id == tweet_id
    ).count()

    liked_by_me = db.query(Like).filter(
        Like.tweet_id == tweet_id,
        Like.user_id == current_user_id
    ).first() is not None

    return like_count, liked_by_me


# ============================================================
# CREATE TWEET
# ============================================================

@router.post(
    "/",
    response_model=TweetResponse,
    status_code=status.HTTP_201_CREATED
)
def create_tweet(
    text: str = Form(...),
    photo: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Remove unnecessary whitespace
    text = text.strip()

    # Validate tweet text
    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tweet cannot be empty"
        )

    if len(text) > 280:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tweet cannot exceed 280 characters"
        )

    # Handle optional image
    photo_path = None

    if photo:
        photo_path = save_image(photo)

    # Create tweet
    tweet = Tweet(
        text=text,
        photo=photo_path,
        user_id=current_user.id
    )

    db.add(tweet)
    db.commit()
    db.refresh(tweet)

    return build_tweet_response(
        tweet=tweet,
        username=current_user.username,
        like_count=0,
        liked_by_me=False
    )


# ============================================================
# GET ALL TWEETS / FEED
# ============================================================

@router.get(
    "/",
    response_model=TweetListResponse
)
def get_tweets(
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
    # Total number of tweets
    total = db.query(Tweet).count()

    # Calculate pagination offset
    offset = (page - 1) * limit

    # Get tweets + usernames
    tweets = (
        db.query(Tweet, User.username)
        .join(
            User,
            Tweet.user_id == User.id
        )
        .order_by(
            Tweet.created_at.desc()
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    tweet_data = []

    for tweet, username in tweets:

        like_count, liked_by_me = get_like_info(
            tweet_id=tweet.id,
            current_user_id=current_user.id,
            db=db
        )

        tweet_data.append(
            build_tweet_response(
                tweet=tweet,
                username=username,
                like_count=like_count,
                liked_by_me=liked_by_me
            )
        )

    has_next = (page * limit) < total

    return TweetListResponse(
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=has_next
    )


# ============================================================
# SEARCH TWEETS
# ============================================================

# IMPORTANT:
# This route must come BEFORE /{tweet_id}
# otherwise "search" can be interpreted as a tweet_id.

@router.get(
    "/search",
    response_model=TweetListResponse
)
def search_tweets(
    q: str = Query(
        ...,
        min_length=1,
        max_length=100
    ),
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
    # Remove unnecessary whitespace
    search_term = q.strip()

    if not search_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )

    search_pattern = f"%{search_term}%"

    # Search both tweet text and username
    query = (
        db.query(Tweet, User.username)
        .join(
            User,
            Tweet.user_id == User.id
        )
        .filter(
            or_(
                Tweet.text.ilike(search_pattern),
                User.username.ilike(search_pattern)
            )
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

    tweet_data = []

    for tweet, username in results:

        like_count, liked_by_me = get_like_info(
            tweet_id=tweet.id,
            current_user_id=current_user.id,
            db=db
        )

        tweet_data.append(
            build_tweet_response(
                tweet=tweet,
                username=username,
                like_count=like_count,
                liked_by_me=liked_by_me
            )
        )

    has_next = (page * limit) < total

    return TweetListResponse(
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=has_next
    )


# ============================================================
# GET ONE TWEET
# ============================================================

@router.get(
    "/{tweet_id}",
    response_model=TweetResponse
)
def get_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = (
        db.query(Tweet, User.username)
        .join(
            User,
            Tweet.user_id == User.id
        )
        .filter(
            Tweet.id == tweet_id
        )
        .first()
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

    tweet, username = result

    like_count, liked_by_me = get_like_info(
        tweet_id=tweet.id,
        current_user_id=current_user.id,
        db=db
    )

    return build_tweet_response(
        tweet=tweet,
        username=username,
        like_count=like_count,
        liked_by_me=liked_by_me
    )


# ============================================================
# UPDATE TWEET
# ============================================================

@router.put(
    "/{tweet_id}",
    response_model=TweetResponse
)
def update_tweet(
    tweet_id: int,
    tweet_data: TweetCreate,
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

    # Only the owner can edit
    if tweet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own tweets"
        )

    text = tweet_data.text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tweet cannot be empty"
        )

    if len(text) > 280:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tweet cannot exceed 280 characters"
        )

    tweet.text = text

    db.commit()
    db.refresh(tweet)

    like_count, liked_by_me = get_like_info(
        tweet_id=tweet.id,
        current_user_id=current_user.id,
        db=db
    )

    return build_tweet_response(
        tweet=tweet,
        username=current_user.username,
        like_count=like_count,
        liked_by_me=liked_by_me
    )


# ============================================================
# DELETE TWEET
# ============================================================

@router.delete(
    "/{tweet_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_tweet(
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

    # Only the owner can delete
    if tweet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tweets"
        )

    # Delete tweet
    db.delete(tweet)
    db.commit()

    return None