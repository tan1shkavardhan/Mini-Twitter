import { useEffect, useState } from "react";
import type { Tweet } from "../api/tweets";
import {
  getFollowers,
  getFollowing,
  type UserSummary,
} from "../api/follows";

interface CurrentUser {
  id: number;
  username: string;
  email: string;
}

interface ProfileProps {
  currentUser: CurrentUser | null;
  tweets: Tweet[];
}

function Profile({
  currentUser,
  tweets,
}: ProfileProps) {
  const [followers, setFollowers] = useState<
    UserSummary[]
  >([]);

  const [following, setFollowing] = useState<
    UserSummary[]
  >([]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadProfileData() {
      if (!currentUser) return;

      try {
        setLoading(true);

        const [followersData, followingData] =
          await Promise.all([
            getFollowers(currentUser.username),
            getFollowing(currentUser.username),
          ]);

        setFollowers(followersData.followers);
        setFollowing(followingData.following);
      } catch (error) {
        console.error(
          "Failed to load profile data",
          error
        );
      } finally {
        setLoading(false);
      }
    }

    loadProfileData();
  }, [currentUser]);

  const myTweets = tweets.filter(
    (tweet) =>
      tweet.user_id === currentUser?.id
  );

  if (!currentUser) {
    return <p>Loading profile...</p>;
  }

  return (
    <div className="profile-page">
      <div className="profile-card">
        <div className="profile-avatar">
          {currentUser.username
            .charAt(0)
            .toUpperCase()}
        </div>

        <h2>@{currentUser.username}</h2>

        <p className="profile-email">
          {currentUser.email}
        </p>

        <div className="profile-stats">
          <div>
            <strong>
              {myTweets.length}
            </strong>
            <span>Posts</span>
          </div>

          <div>
            <strong>
              {followers.length}
            </strong>
            <span>Followers</span>
          </div>

          <div>
            <strong>
              {following.length}
            </strong>
            <span>Following</span>
          </div>
        </div>
      </div>

      {loading ? (
        <p>Loading profile...</p>
      ) : (
        <>
          <div className="profile-lists">
            <div className="profile-list">
              <h3>Followers</h3>

              {followers.length === 0 ? (
                <p className="placeholder">
                  No followers yet.
                </p>
              ) : (
                followers.map((user) => (
                  <div
                    className="profile-user"
                    key={user.id}
                  >
                    @{user.username}
                  </div>
                ))
              )}
            </div>

            <div className="profile-list">
              <h3>Following</h3>

              {following.length === 0 ? (
                <p className="placeholder">
                  Not following anyone yet.
                </p>
              ) : (
                following.map((user) => (
                  <div
                    className="profile-user"
                    key={user.id}
                  >
                    @{user.username}
                  </div>
                ))
              )}
            </div>
          </div>

          <h3 className="profile-title">
            Your Posts
          </h3>

          {myTweets.length === 0 && (
            <p className="placeholder">
              You haven't posted anything yet.
            </p>
          )}

          {myTweets.map((tweet) => (
            <div
              className="tweet"
              key={tweet.id}
            >
              <div className="tweet-header">
                <strong>
                  @{tweet.username}
                </strong>

                <span>
                  ·{" "}
                  {new Date(
                    tweet.created_at
                  ).toLocaleString()}
                </span>
              </div>

              <p>{tweet.text}</p>

              {tweet.photo && (
                <img
                  src={`http://127.0.0.1:8000/${tweet.photo.replace(
                    /\\/g,
                    "/"
                  )}`}
                  alt="Tweet attachment"
                  className="tweet-photo"
                />
              )}

              <div className="tweet-actions">
                <span>
                  💬 {tweet.comment_count}
                </span>

                <span>
                  {tweet.liked_by_me
                    ? "❤️"
                    : "🤍"}{" "}
                  {tweet.like_count}
                </span>
              </div>
            </div>
          ))}
        </>
      )}
    </div>
  );
}

export default Profile;