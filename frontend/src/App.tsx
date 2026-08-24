import { useEffect, useState } from "react";

import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";

import {
  createTweet,
  deleteTweet,
  getTweets,
  updateTweet,
  likeTweet,
  unlikeTweet,
  type Tweet,
} from "./api/tweets";

import {
  getComments,
  createComment,
  type Comment,
} from "./api/comments";

import { getCurrentUser } from "./api/auth";

import Explore from "./components/Explore";

import Profile from "./components/Profile";

import "./App.css";

interface CurrentUser {
  id: number;
  username: string;
  email: string;
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("access_token")
  );

  const [showLogin, setShowLogin] = useState(true);
  const [activeTab, setActiveTab] = useState("Home");

  const [tweets, setTweets] = useState<Tweet[]>([]);
  const [tweetText, setTweetText] = useState("");

  const [selectedPhoto, setSelectedPhoto] =
    useState<File | undefined>(undefined);

  const [loadingTweets, setLoadingTweets] =
    useState(false);

  const [posting, setPosting] = useState(false);

  const [currentUser, setCurrentUser] =
    useState<CurrentUser | null>(null);

  const [editingTweetId, setEditingTweetId] =
    useState<number | null>(null);

  const [editingText, setEditingText] =
    useState("");

  const [openComments, setOpenComments] =
    useState<number | null>(null);

  const [comments, setComments] = useState<
    Record<number, Comment[]>
  >({});

  const [commentText, setCommentText] = useState<
    Record<number, string>
  >({});

  const [loadingComments, setLoadingComments] =
    useState<number | null>(null);

  const [postingComment, setPostingComment] =
    useState<number | null>(null);

  async function loadTweets() {
    try {
      setLoadingTweets(true);

      const data = await getTweets();

      setTweets(data.tweets);
    } catch (error) {
      console.error("Failed to load tweets", error);
    } finally {
      setLoadingTweets(false);
    }
  }

  async function loadCurrentUser() {
    try {
      const user = await getCurrentUser();

      setCurrentUser(user);
    } catch (error) {
      console.error(
        "Failed to load current user",
        error
      );
    }
  }

  async function handleCreateTweet() {
    if (!tweetText.trim()) return;

    try {
      setPosting(true);

      const newTweet = await createTweet(
        tweetText,
        selectedPhoto
      );

      setTweets((currentTweets) => [
        newTweet,
        ...currentTweets,
      ]);

      setTweetText("");
      setSelectedPhoto(undefined);
    } catch (error) {
      console.error(
        "Failed to create tweet",
        error
      );
    } finally {
      setPosting(false);
    }
  }

  async function handleLike(tweet: Tweet) {
    try {
      if (tweet.liked_by_me) {
        await unlikeTweet(tweet.id);
      } else {
        await likeTweet(tweet.id);
      }

      setTweets((currentTweets) =>
        currentTweets.map((currentTweet) => {
          if (currentTweet.id !== tweet.id) {
            return currentTweet;
          }

          return {
            ...currentTweet,
            liked_by_me:
              !currentTweet.liked_by_me,

            like_count:
              currentTweet.liked_by_me
                ? currentTweet.like_count - 1
                : currentTweet.like_count + 1,
          };
        })
      );
    } catch (error) {
      console.error(
        "Failed to update like",
        error
      );
    }
  }

  async function handleToggleComments(
    tweetId: number
  ) {
    if (openComments === tweetId) {
      setOpenComments(null);
      return;
    }

    setOpenComments(tweetId);

    if (comments[tweetId]) return;

    try {
      setLoadingComments(tweetId);

      const data = await getComments(tweetId);

      setComments((currentComments) => ({
        ...currentComments,
        [tweetId]: data.comments,
      }));
    } catch (error) {
      console.error(
        "Failed to load comments",
        error
      );
    } finally {
      setLoadingComments(null);
    }
  }

  async function handleCreateComment(
    tweetId: number
  ) {
    const text = commentText[tweetId]?.trim();

    if (!text) return;

    try {
      setPostingComment(tweetId);

      const newComment = await createComment(
        tweetId,
        text
      );

      setComments((currentComments) => ({
        ...currentComments,
        [tweetId]: [
          ...(currentComments[tweetId] || []),
          newComment,
        ],
      }));

      setCommentText((currentText) => ({
        ...currentText,
        [tweetId]: "",
      }));

      setTweets((currentTweets) =>
        currentTweets.map((tweet) =>
          tweet.id === tweetId
            ? {
                ...tweet,
                comment_count:
                  tweet.comment_count + 1,
              }
            : tweet
        )
      );
    } catch (error) {
      console.error(
        "Failed to create comment",
        error
      );
    } finally {
      setPostingComment(null);
    }
  }

  function startEditing(tweet: Tweet) {
    setEditingTweetId(tweet.id);
    setEditingText(tweet.text);
  }

  function cancelEditing() {
    setEditingTweetId(null);
    setEditingText("");
  }

  async function handleUpdateTweet(
    tweetId: number
  ) {
    if (!editingText.trim()) return;

    try {
      const updatedTweet = await updateTweet(
        tweetId,
        editingText
      );

      setTweets((currentTweets) =>
        currentTweets.map((tweet) =>
          tweet.id === tweetId
            ? updatedTweet
            : tweet
        )
      );

      cancelEditing();
    } catch (error) {
      console.error(
        "Failed to update tweet",
        error
      );
    }
  }

  async function handleDeleteTweet(
    tweetId: number
  ) {
    const confirmed = window.confirm(
      "Delete this tweet?"
    );

    if (!confirmed) return;

    try {
      await deleteTweet(tweetId);

      setTweets((currentTweets) =>
        currentTweets.filter(
          (tweet) => tweet.id !== tweetId
        )
      );

      setComments((currentComments) => {
        const updatedComments = {
          ...currentComments,
        };

        delete updatedComments[tweetId];

        return updatedComments;
      });
    } catch (error) {
      console.error(
        "Failed to delete tweet",
        error
      );
    }
  }

  function handleLogout() {
    localStorage.removeItem("access_token");

    setIsLoggedIn(false);
    setShowLogin(true);
    setTweets([]);
    setCurrentUser(null);
    setComments({});
    setOpenComments(null);
  }

  useEffect(() => {
    if (isLoggedIn) {
      loadTweets();
      loadCurrentUser();
    }
  }, [isLoggedIn]);

  if (!isLoggedIn) {
    if (showLogin) {
      return (
        <LoginPage
          onLoginSuccess={() =>
            setIsLoggedIn(true)
          }
          onSwitchToRegister={() =>
            setShowLogin(false)
          }
        />
      );
    }

    return (
      <RegisterPage
        onSwitchToLogin={() =>
          setShowLogin(true)
        }
      />
    );
  }

  const myTweets = tweets.filter(
    (tweet) =>
      tweet.user_id === currentUser?.id
  );

  return (
    <div className="app">
      <aside className="sidebar">
        <h1 className="logo">
          MiniTwitter
        </h1>

        <nav>
          <button
            className={
              activeTab === "Home"
                ? "active"
                : ""
            }
            onClick={() =>
              setActiveTab("Home")
            }
          >
            🏠 Home
          </button>

          <button
            className={
              activeTab === "Profile"
                ? "active"
                : ""
            }
            onClick={() =>
              setActiveTab("Profile")
            }
          >
            👤 Profile
          </button>

          <button
            className={
              activeTab === "Explore"
                ? "active"
                : ""
            }
            onClick={() =>
              setActiveTab("Explore")
            }
          >
            🔍 Explore
          </button>
        </nav>

        <button
          className="logout"
          onClick={handleLogout}
        >
          Logout
        </button>
      </aside>

      <main className="feed">
        <header>
          <h2>{activeTab}</h2>
        </header>

        {activeTab === "Home" && (
          <>
            <div className="create-tweet">
              <textarea
                placeholder="What's happening?"
                value={tweetText}
                onChange={(event) =>
                  setTweetText(
                    event.target.value
                  )
                }
              />

              <input
                type="file"
                accept="image/jpeg,image/png"
                onChange={(event) => {
                  const file =
                    event.target.files?.[0];

                  if (file) {
                    setSelectedPhoto(file);
                  }
                }}
              />

              {selectedPhoto && (
                <p>
                  Selected: {selectedPhoto.name}
                </p>
              )}

              <button
                onClick={handleCreateTweet}
                disabled={
                  posting ||
                  !tweetText.trim()
                }
              >
                {posting
                  ? "Posting..."
                  : "Post"}
              </button>
            </div>

            {loadingTweets && (
              <p>Loading tweets...</p>
            )}

            {!loadingTweets &&
              tweets.map((tweet) => {
                const isOwner =
                  currentUser?.id ===
                  tweet.user_id;

                const isEditing =
                  editingTweetId ===
                  tweet.id;

                return (
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

                    {isEditing ? (
                      <>
                        <textarea
                          value={editingText}
                          onChange={(event) =>
                            setEditingText(
                              event.target.value
                            )
                          }
                        />

                        <div className="edit-actions">
                          <button
                            onClick={() =>
                              handleUpdateTweet(
                                tweet.id
                              )
                            }
                            disabled={
                              !editingText.trim()
                            }
                          >
                            Save
                          </button>

                          <button
                            onClick={cancelEditing}
                          >
                            Cancel
                          </button>
                        </div>
                      </>
                    ) : (
                      <p>{tweet.text}</p>
                    )}

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
                      <button
                        onClick={() =>
                          handleToggleComments(
                            tweet.id
                          )
                        }
                      >
                        💬 {tweet.comment_count}
                      </button>

                      <button
                        onClick={() =>
                          handleLike(tweet)
                        }
                      >
                        {tweet.liked_by_me
                          ? "❤️"
                          : "🤍"}{" "}
                        {tweet.like_count}
                      </button>

                      {isOwner &&
                        !isEditing && (
                          <>
                            <button
                              onClick={() =>
                                startEditing(tweet)
                              }
                            >
                              ✏️ Edit
                            </button>

                            <button
                              onClick={() =>
                                handleDeleteTweet(
                                  tweet.id
                                )
                              }
                            >
                              🗑️ Delete
                            </button>
                          </>
                        )}
                    </div>

                    {openComments ===
                      tweet.id && (
                      <div className="comments-section">
                        {loadingComments ===
                          tweet.id && (
                          <p>
                            Loading comments...
                          </p>
                        )}

                        {!loadingComments &&
                          comments[
                            tweet.id
                          ]?.map((comment) => (
                            <div
                              className="comment"
                              key={comment.id}
                            >
                              <strong>
                                @{comment.username}
                              </strong>

                              <p>
                                {comment.text}
                              </p>
                            </div>
                          ))}

                        {!loadingComments &&
                          comments[
                            tweet.id
                          ]?.length === 0 && (
                            <p className="placeholder">
                              No comments yet.
                            </p>
                          )}

                        <div className="add-comment">
                          <input
                            type="text"
                            placeholder="Write a comment..."
                            value={
                              commentText[
                                tweet.id
                              ] || ""
                            }
                            onChange={(event) =>
                              setCommentText(
                                (currentText) => ({
                                  ...currentText,
                                  [tweet.id]:
                                    event.target
                                      .value,
                                })
                              )
                            }
                          />

                          <button
                            onClick={() =>
                              handleCreateComment(
                                tweet.id
                              )
                            }
                            disabled={
                              postingComment ===
                                tweet.id ||
                              !commentText[
                                tweet.id
                              ]?.trim()
                            }
                          >
                            {postingComment ===
                            tweet.id
                              ? "Posting..."
                              : "Comment"}
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
          </>
        )}

      {activeTab === "Profile" && (
        <Profile
          currentUser={currentUser}
          tweets={tweets}
        />
      )}

      {activeTab === "Explore" && (
        <Explore tweets={tweets} 
        currentUser = {currentUser} />
      )}
      </main>
    </div>
  );
}

export default App;