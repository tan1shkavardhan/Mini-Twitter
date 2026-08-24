import { useEffect, useMemo, useState } from "react";
import type { Tweet } from "../api/tweets";
import {
  followUser,
  getFollowing,
  unfollowUser,
} from "../api/follows";

interface CurrentUser {
  id: number;
  username: string;
  email: string;
}

interface ExploreProps {
  tweets: Tweet[];
  currentUser: CurrentUser | null;
}

function Explore({
  tweets,
  currentUser,
}: ExploreProps) {
  const [searchInput, setSearchInput] = useState("");
  const [query, setQuery] = useState("");
  const [following, setFollowing] = useState<string[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [updatingUser, setUpdatingUser] =
    useState<string | null>(null);

  useEffect(() => {
    async function loadFollowing() {
      if (!currentUser) return;

      try {
        setLoadingUsers(true);

        const data = await getFollowing(
          currentUser.username
        );

        setFollowing(
          data.following.map(
            (user) => user.username
          )
        );
      } catch (error) {
        console.error(
          "Failed to load following users",
          error
        );
      } finally {
        setLoadingUsers(false);
      }
    }

    loadFollowing();
  }, [currentUser]);

  const filteredTweets = tweets.filter((tweet) => {
    const searchText = query.trim().toLowerCase();

    if (!searchText) return true;

    return (
      tweet.username
        .toLowerCase()
        .includes(searchText) ||
      tweet.text
        .toLowerCase()
        .includes(searchText)
    );
  });

  const users = useMemo(() => {
    const uniqueUsers = new Map<
      number,
      { id: number; username: string }
    >();

    tweets.forEach((tweet) => {
      if (
        tweet.user_id !== currentUser?.id &&
        !uniqueUsers.has(tweet.user_id)
      ) {
        uniqueUsers.set(tweet.user_id, {
          id: tweet.user_id,
          username: tweet.username,
        });
      }
    });

    return Array.from(uniqueUsers.values());
  }, [tweets, currentUser]);

  async function handleFollow(
    username: string
  ) {
    try {
      setUpdatingUser(username);

      if (following.includes(username)) {
        await unfollowUser(username);

        setFollowing((current) =>
          current.filter(
            (user) => user !== username
          )
        );
      } else {
        await followUser(username);

        setFollowing((current) => [
          ...current,
          username,
        ]);
      }
    } catch (error) {
      console.error(
        "Failed to update follow status",
        error
      );
    } finally {
      setUpdatingUser(null);
    }
  }

  function handleSearch() {
    setQuery(searchInput);
  }

  function handleClear() {
    setSearchInput("");
    setQuery("");
  }

  function handleKeyDown(
    event: React.KeyboardEvent<HTMLInputElement>
  ) {
    if (event.key === "Enter") {
      handleSearch();
    }
  }

  return (
    <div className="explore-page">
      <h2>Explore</h2>

      <div className="search-container">
        <input
          type="text"
          placeholder="Search tweets or users..."
          value={searchInput}
          onChange={(event) =>
            setSearchInput(event.target.value)
          }
          onKeyDown={handleKeyDown}
          className="search-input"
        />

        <button
          className="search-button"
          onClick={handleSearch}
        >
          Search
        </button>

        {query && (
          <button
            className="clear-search"
            onClick={handleClear}
          >
            Clear
          </button>
        )}
      </div>

      <div className="users-section">
        <h3>People</h3>

        {loadingUsers && (
          <p>Loading users...</p>
        )}

        {!loadingUsers &&
          users.map((user) => {
            const isFollowing =
              following.includes(
                user.username
              );

            const isUpdating =
              updatingUser === user.username;

            return (
              <div
                className="user-card"
                key={user.id}
              >
                <strong>
                  @{user.username}
                </strong>

                <button
                  onClick={() =>
                    handleFollow(user.username)
                  }
                  disabled={isUpdating}
                >
                  {isUpdating
                    ? "Updating..."
                    : isFollowing
                    ? "Unfollow"
                    : "Follow"}
                </button>
              </div>
            );
          })}

        {!loadingUsers &&
          users.length === 0 && (
            <p className="placeholder">
              No other users yet.
            </p>
          )}
      </div>

      <div className="explore-results">
        <h3>Posts</h3>

        {filteredTweets.map((tweet) => (
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
                ❤️ {tweet.like_count}
              </span>
            </div>
          </div>
        ))}

        {query &&
          filteredTweets.length === 0 && (
            <p className="placeholder">
              No results found for "{query}".
            </p>
          )}
      </div>
    </div>
  );
}

export default Explore;