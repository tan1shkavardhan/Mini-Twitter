import { Heart, MessageCircle, Repeat2, Share } from "lucide-react";
import { useState } from "react";

import {
  likeTweet,
  unlikeTweet,
  type Tweet,
} from "../api/tweets";

interface TweetCardProps {
  tweet: Tweet;
  onLikeChanged: () => void;
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  const now = new Date();

  const difference = now.getTime() - date.getTime();
  const minutes = Math.floor(difference / 60000);

  if (minutes < 1) {
    return "now";
  }

  if (minutes < 60) {
    return `${minutes}m`;
  }

  const hours = Math.floor(minutes / 60);

  if (hours < 24) {
    return `${hours}h`;
  }

  const days = Math.floor(hours / 24);

  return `${days}d`;
}

function TweetCard({
  tweet,
  onLikeChanged,
}: TweetCardProps) {
  const [likeLoading, setLikeLoading] = useState(false);

  const photoUrl = tweet.photo
    ? `http://localhost:8000/${tweet.photo.replace(/^\/+/, "")}`
    : null;

  const handleLike = async () => {
    if (likeLoading) return;

    setLikeLoading(true);

    try {
      if (tweet.liked_by_me) {
        await unlikeTweet(tweet.id);
      } else {
        await likeTweet(tweet.id);
      }

      // Reload tweets so the like count and liked state update
      onLikeChanged();
    } catch (error) {
      console.error("Failed to update like:", error);
    } finally {
      setLikeLoading(false);
    }
  };

  return (
    <article className="tweet-card">
      <div className="tweet-avatar">
        {tweet.username.charAt(0).toUpperCase()}
      </div>

      <div className="tweet-content">
        <div className="tweet-header">
          <strong>{tweet.username}</strong>

          <span>@{tweet.username}</span>

          <span className="tweet-dot">·</span>

          <span>{formatDate(tweet.created_at)}</span>
        </div>

        <p className="tweet-text">
          {tweet.text}
        </p>

        {tweet.hashtags?.length > 0 && (
          <div className="hashtags">
            {tweet.hashtags.map((hashtag) => (
              <span key={hashtag.id}>
                #{hashtag.name}
              </span>
            ))}
          </div>
        )}

        {photoUrl && (
          <img
            src={photoUrl}
            alt="Tweet attachment"
            className="tweet-image"
          />
        )}

        <div className="tweet-actions">
          {/* Comments - backend wiring later */}
          <button>
            <MessageCircle size={18} />
            <span>{tweet.comment_count}</span>
          </button>

          {/* Reposts - backend wiring later */}
          <button>
            <Repeat2 size={18} />
            <span>{tweet.repost_count ?? 0}</span>
          </button>

          {/* LIKE / UNLIKE */}
          <button
            className={
              tweet.liked_by_me ? "liked" : ""
            }
            onClick={handleLike}
            disabled={likeLoading}
          >
            <Heart
              size={18}
              fill={
                tweet.liked_by_me
                  ? "currentColor"
                  : "none"
              }
            />

            <span>{tweet.like_count}</span>
          </button>

          {/* Share - frontend only for now */}
          <button>
            <Share size={18} />
          </button>
        </div>
      </div>
    </article>
  );
}

export default TweetCard;