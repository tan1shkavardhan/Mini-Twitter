import {
  useEffect,
  useState,
} from "react";

import {
  LoaderCircle,
  Search,
} from "lucide-react";

import Sidebar from "../components/Sidebar";
import TweetComposer from "../components/TweetComposer";
import TweetCard from "../components/TweetCard";

import {
  getTweets,
  type Tweet,
} from "../api/tweets";

function Home() {
  const [tweets, setTweets] =
    useState<Tweet[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");

  const loadTweets = async () => {
    try {
      setError("");

      const data =
        await getTweets();

      setTweets(data.tweets);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Unable to load ripples."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTweets();
  }, []);

  return (
    <div className="app-layout">
      <Sidebar />

      <main className="main-feed">
        <div className="feed-header">
          <h1>Home</h1>

          <p>
            See what's creating ripples.
          </p>
        </div>

        <TweetComposer
          onTweetCreated={loadTweets}
        />

        <div className="feed">
          {loading && (
            <div className="loading-state">
              <LoaderCircle
                className="spinner"
                size={28}
              />

              <p>
                Loading ripples...
              </p>
            </div>
          )}

          {error && (
            <div className="feed-error">
              {error}
            </div>
          )}

          {!loading &&
            !error &&
            tweets.length === 0 && (
              <div className="empty-feed">
                <h2>
                  No ripples yet
                </h2>

                <p>
                  Be the first person to
                  start a conversation.
                </p>
              </div>
            )}

          {tweets.map(
            (tweet) => (
              <TweetCard
                key={tweet.id}
                tweet={tweet}
                onLikeChanged={loadTweets}
              />
            )
          )}
        </div>
      </main>

      <aside className="right-sidebar">
        <div className="search-box">
          <Search size={19} />

          <input
            placeholder="Search Ripple"
          />
        </div>

        <div className="side-card">
          <h3>
            What's happening
          </h3>

          <div className="trend">
            <span>
              Trending now
            </span>

            <strong>
              #Ripple
            </strong>

            <small>
              Join the conversation
            </small>
          </div>

          <div className="trend">
            <span>
              Trending now
            </span>

            <strong>
              #Technology
            </strong>

            <small>
              Explore new ideas
            </small>
          </div>

          <div className="trend">
            <span>
              Trending now
            </span>

            <strong>
              #CampusLife
            </strong>

            <small>
              Share your story
            </small>
          </div>
        </div>
      </aside>
    </div>
  );
}

export default Home;