import io
import os
import re
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

from PIL import Image, UnidentifiedImageError

from sqlalchemy import (
    and_,
    exists,
    func,
    or_
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

from app.schemas import (
    HashtagResponse,
    TweetCreate,
    TweetListResponse,
    TweetResponse
)


# ============================================================
# CONSTANTS
# ============================================================

MAX_IMAGE_SIZE = 5 * 1024 * 1024

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
# IMAGE HANDLING
# ============================================================

def save_image(photo: UploadFile) -> str:

    if photo.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG and WebP images are allowed"
        )

    extension = os.path.splitext(
        photo.filename or ""
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Allowed image extensions: .jpg, .jpeg, .png, .webp"
        )

    try:

        total_size = 0
        file_data = bytearray()

        while True:

            chunk = photo.file.read(
                1024 * 1024
            )

            if not chunk:
                break

            total_size += len(chunk)

            if total_size > MAX_IMAGE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="Image size cannot exceed 5 MB"
                )

            file_data.extend(chunk)

        if total_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image cannot be empty"
            )

    finally:
        photo.file.close()

    try:

        image = Image.open(
            io.BytesIO(file_data)
        )

        detected_format = image.format

        image.verify()

    except (
        UnidentifiedImageError,
        OSError,
        SyntaxError
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is not a valid image"
        )

    format_to_content_type = {
        "JPEG": "image/jpeg",
        "PNG": "image/png",
        "WEBP": "image/webp"
    }

    detected_content_type = format_to_content_type.get(
        detected_format
    )

    if detected_content_type != photo.content_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File content does not match its declared type"
        )

    os.makedirs(
        "uploads",
        exist_ok=True
    )

    filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        "uploads",
        filename
    )

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:
            buffer.write(file_data)

    except Exception:

        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save image"
        )

    return file_path


# ============================================================
# HASHTAGS
# ============================================================

def extract_hashtags(
    text: str
) -> list[str]:

    hashtags = re.findall(
        r"#([A-Za-z0-9_]+)",
        text
    )

    return list(
        dict.fromkeys(
            hashtag.lower()
            for hashtag in hashtags
        )
    )


def sync_tweet_hashtags(
    db: Session,
    tweet: Tweet,
    text: str
) -> None:

    hashtag_names = extract_hashtags(
        text
    )

    tweet.hashtags.clear()

    for name in hashtag_names:

        hashtag = (
            db.query(Hashtag)
            .filter(
                Hashtag.name == name
            )
            .first()
        )

        if not hashtag:

            hashtag = Hashtag(
                name=name
            )

            db.add(hashtag)
            db.flush()

        tweet.hashtags.append(
            hashtag
        )


# ============================================================
# RESPONSE BUILDER
# ============================================================

def build_tweet_response(
    tweet: Tweet,
    username: str,
    like_count: int,
    liked_by_me: bool,
    comment_count: int,
    repost_count: int,
    reposted_by_me: bool
) -> TweetResponse:

    hashtags = [
        HashtagResponse(
            id=hashtag.id,
            name=hashtag.name
        )
        for hashtag in tweet.hashtags
    ]

    return TweetResponse(
        id=tweet.id,
        user_id=tweet.user_id,
        username=username,
        text=tweet.text,
        photo=tweet.photo,
        created_at=tweet.created_at,
        updated_at=tweet.updated_at,

        like_count=like_count,
        liked_by_me=liked_by_me,

        comment_count=comment_count,

        hashtags=hashtags,

        repost_count=repost_count,
        reposted_by_me=reposted_by_me
    )


# ============================================================
# OPTIMIZED TWEET QUERY
# ============================================================

def get_tweet_query(
    db: Session,
    current_user_id: int
):

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
            Like.user_id == current_user_id
        )
    )

    reposted_by_me_subquery = exists().where(
        and_(
            Repost.tweet_id == Tweet.id,
            Repost.user_id == current_user_id
        )
    )

    query = (
        db.query(
            Tweet,
            User.username,

            func.coalesce(
                like_count_subquery.c.like_count,
                0
            ).label(
                "like_count"
            ),

            func.coalesce(
                comment_count_subquery.c.comment_count,
                0
            ).label(
                "comment_count"
            ),

            func.coalesce(
                repost_count_subquery.c.repost_count,
                0
            ).label(
                "repost_count"
            ),

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

    return query


# ============================================================
# QUERY RESULT → RESPONSE
# ============================================================

def make_tweet_response(
    result
) -> TweetResponse:

    (
        tweet,
        username,
        like_count,
        comment_count,
        repost_count,
        liked_by_me,
        reposted_by_me
    ) = result

    return build_tweet_response(
        tweet=tweet,
        username=username,
        like_count=like_count,
        liked_by_me=bool(liked_by_me),
        comment_count=comment_count,
        repost_count=repost_count,
        reposted_by_me=bool(reposted_by_me)
    )


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

    text = text.strip()

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

    photo_path = None

    if photo:
        photo_path = save_image(
            photo
        )

    tweet = Tweet(
        text=text,
        photo=photo_path,
        user_id=current_user.id
    )

    db.add(tweet)

    sync_tweet_hashtags(
        db,
        tweet,
        text
    )

    db.commit()
    db.refresh(tweet)

    return build_tweet_response(
        tweet=tweet,
        username=current_user.username,
        like_count=0,
        liked_by_me=False,
        comment_count=0,
        repost_count=0,
        reposted_by_me=False
    )


# ============================================================
# GET ALL TWEETS
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

    query = get_tweet_query(
        db,
        current_user.id
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
        make_tweet_response(
            result
        )
        for result in results
    ]

    return TweetListResponse(
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total
    )


# ============================================================
# SEARCH TWEETS
# ============================================================

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

    search_term = q.strip()

    if not search_term:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query cannot be empty"
        )

    search_pattern = f"%{search_term}%"

    query = (
        get_tweet_query(
            db,
            current_user.id
        )
        .filter(
            or_(
                Tweet.text.ilike(
                    search_pattern
                ),
                User.username.ilike(
                    search_pattern
                )
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

    tweet_data = [
        make_tweet_response(
            result
        )
        for result in results
    ]

    return TweetListResponse(
        tweets=tweet_data,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total
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

    query = (
        get_tweet_query(
            db,
            current_user.id
        )
        .filter(
            Tweet.id == tweet_id
        )
    )

    result = query.first()

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

    return make_tweet_response(
        result
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

    tweet = (
        db.query(Tweet)
        .filter(
            Tweet.id == tweet_id
        )
        .first()
    )

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

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

    sync_tweet_hashtags(
        db,
        tweet,
        text
    )

    db.commit()
    db.refresh(tweet)

    query = (
        get_tweet_query(
            db,
            current_user.id
        )
        .filter(
            Tweet.id == tweet.id
        )
    )

    result = query.first()

    return make_tweet_response(
        result
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

    tweet = (
        db.query(Tweet)
        .filter(
            Tweet.id == tweet_id
        )
        .first()
    )

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )

    if tweet.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own tweets"
        )

    db.delete(tweet)
    db.commit()

    return None