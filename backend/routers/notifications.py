from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Notification, User
from app.schemas import (
    NotificationListResponse,
    NotificationResponse,
)


router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"]
)


# ============================================================
# GET MY NOTIFICATIONS
# ============================================================

@router.get(
    "",
    response_model=NotificationListResponse
)
def get_notifications(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = (
        db.query(Notification, User.username)
        .join(
            User,
            Notification.actor_id == User.id
        )
        .filter(
            Notification.user_id == current_user.id
        )
    )

    total = query.count()

    offset = (page - 1) * limit

    results = (
        query
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    notifications = [
        NotificationResponse(
            id=notification.id,
            actor_id=notification.actor_id,
            actor_username=username,
            type=notification.type,
            tweet_id=notification.tweet_id,
            comment_id=notification.comment_id,
            is_read=bool(notification.is_read),
            created_at=notification.created_at,
        )
        for notification, username in results
    ]

    return NotificationListResponse(
        notifications=notifications,
        page=page,
        limit=limit,
        total=total,
        has_next=(page * limit) < total,
    )

# ============================================================
# MARK ONE NOTIFICATION AS READ
# ============================================================

@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse
)
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
        .first()
    )

    if not notification:
        raise HTTPException(
            status_code=404,
            detail="Notification not found"
        )

    notification.is_read = 1

    db.commit()
    db.refresh(notification)

    actor = db.query(User).filter(
        User.id == notification.actor_id
    ).first()

    return NotificationResponse(
        id=notification.id,
        actor_id=notification.actor_id,
        actor_username=actor.username,
        type=notification.type,
        tweet_id=notification.tweet_id,
        comment_id=notification.comment_id,
        is_read=bool(notification.is_read),
        created_at=notification.created_at,
    )

# ============================================================
# MARK ALL NOTIFICATIONS AS READ
# ============================================================

@router.patch(
    "/read-all"
)
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    unread_notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == 0
        )
        .all()
    )

    for notification in unread_notifications:
        notification.is_read = 1

    db.commit()

    return {
        "message": "All notifications marked as read",
        "updated_count": len(unread_notifications)
    }