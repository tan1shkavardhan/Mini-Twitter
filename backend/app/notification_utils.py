from sqlalchemy.orm import Session

from app.models import Notification


def create_notification(
    db: Session,
    user_id: int,
    actor_id: int,
    notification_type: str,
    tweet_id: int | None = None,
    comment_id: int | None = None,
):
    # Don't notify yourself about your own action
    if user_id == actor_id:
        return None

    notification = Notification(
        user_id=user_id,
        actor_id=actor_id,
        type=notification_type,
        tweet_id=tweet_id,
        comment_id=comment_id,
    )

    db.add(notification)

    return notification