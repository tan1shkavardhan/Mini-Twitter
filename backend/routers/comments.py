from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Comment, Tweet, User
from app.schemas import (
    CommentCreate,
    CommentListResponse,
    CommentResponse,
)
from app.notification_utils import create_notification


router = APIRouter(tags=["Comments"])


# ============================================================
# HELPERS
# ============================================================

def get_reply_count(
    db: Session,
    comment_id: int
) -> int:
    return (
        db.query(Comment)
        .filter(Comment.parent_comment_id == comment_id)
        .count()
    )


def build_comment_response(
    comment: Comment,
    username: str,
    db: Session
) -> CommentResponse:
    return CommentResponse(
        id=comment.id,
        user_id=comment.user_id,
        username=username,
        tweet_id=comment.tweet_id,
        parent_comment_id=comment.parent_comment_id,
        text=comment.text,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        reply_count=get_reply_count(db, comment.id),
    )


# ============================================================
# CREATE COMMENT / REPLY
# ============================================================

@router.post(
    "/tweets/{tweet_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    tweet_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tweet = db.query(Tweet).filter(
        Tweet.id == tweet_id
    ).first()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found",
        )

    text = comment_data.text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot be empty",
        )

    parent_comment=None

    # Validate parent comment when creating a reply
    if comment_data.parent_comment_id is not None:

        parent_comment = (
            db.query(Comment)
            .filter(
                Comment.id == comment_data.parent_comment_id
            )
            .first()
        )

        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent comment not found",
            )

        # Parent must belong to the same tweet
        if parent_comment.tweet_id != tweet_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent comment belongs to another tweet",
            )

    comment = Comment(
        user_id=current_user.id,
        tweet_id=tweet_id,
        parent_comment_id=comment_data.parent_comment_id,
        text=text,
    )

    db.add(comment)
    db.flush()
    # If this is a reply, notify the parent comment owner
    if parent_comment:
        create_notification(
            db=db,
            user_id=parent_comment.user_id,
            actor_id=current_user.id,
            notification_type="reply",
            tweet_id=tweet_id,
            comment_id=comment.id,
        )

    # Otherwise, notify the tweet owner
    else:
        create_notification(
            db=db,
            user_id=tweet.user_id,
            actor_id=current_user.id,
            notification_type="comment",
            tweet_id=tweet_id,
            comment_id=comment.id,
        )

    db.commit()
    db.refresh(comment)

    return build_comment_response(
        comment,
        current_user.username,
        db,
    )


# ============================================================
# GET TOP-LEVEL COMMENTS
# ============================================================

@router.get(
    "/tweets/{tweet_id}/comments",
    response_model=CommentListResponse,
)
def get_comments(
    tweet_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    tweet = db.query(Tweet).filter(
        Tweet.id == tweet_id
    ).first()

    if not tweet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found",
        )

    query = db.query(Comment).filter(
        Comment.tweet_id == tweet_id,
        Comment.parent_comment_id.is_(None),
    )

    total = query.count()

    offset = (page - 1) * limit

    results = (
        db.query(Comment, User.username)
        .join(User, Comment.user_id == User.id)
        .filter(
            Comment.tweet_id == tweet_id,
            Comment.parent_comment_id.is_(None),
        )
        .order_by(Comment.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    comments = [
        build_comment_response(
            comment,
            username,
            db,
        )
        for comment, username in results
    ]

    return CommentListResponse(
        comments=comments,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total,
    )


# ============================================================
# GET REPLIES TO A COMMENT
# ============================================================

@router.get(
    "/comments/{comment_id}/replies",
    response_model=CommentListResponse,
)
def get_replies(
    comment_id: int,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    parent_comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not parent_comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    query = db.query(Comment).filter(
        Comment.parent_comment_id == comment_id
    )

    total = query.count()
    offset = (page - 1) * limit

    results = (
        db.query(Comment, User.username)
        .join(User, Comment.user_id == User.id)
        .filter(
            Comment.parent_comment_id == comment_id
        )
        .order_by(Comment.created_at.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    comments = [
        build_comment_response(
            comment,
            username,
            db,
        )
        for comment, username in results
    ]

    return CommentListResponse(
        comments=comments,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total,
    )


# ============================================================
# UPDATE COMMENT
# ============================================================

@router.put(
    "/comments/{comment_id}",
    response_model=CommentResponse,
)
def update_comment(
    comment_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = db.query(Comment).filter(
        Comment.id == comment_id
    ).first()

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own comments",
        )

    text = comment_data.text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Comment cannot be empty",
        )

    comment.text = text

    db.commit()
    db.refresh(comment)

    return build_comment_response(
        comment,
        current_user.username,
        db,
    )


# ============================================================
# DELETE COMMENT
# ============================================================

def delete_comment_tree(
    db: Session,
    comment_id: int,
):
    replies = (
        db.query(Comment)
        .filter(Comment.parent_comment_id == comment_id)
        .all()
    )

    # Recursively delete replies of replies
    for reply in replies:
        delete_comment_tree(
            db,
            reply.id,
        )

    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id)
        .first()
    )

    if comment:
        db.delete(comment)


@router.delete(
    "/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    comment = (
        db.query(Comment)
        .filter(Comment.id == comment_id)
        .first()
    )

    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )

    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own comments",
        )

    delete_comment_tree(
        db,
        comment_id,
    )

    db.commit()

    return None