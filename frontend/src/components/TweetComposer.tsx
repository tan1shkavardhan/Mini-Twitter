import {
  Image,
  Send,
  X,
} from "lucide-react";

import {
  useRef,
  useState,
} from "react";

interface TweetComposerProps {
  onTweetCreated: () => void;
}

function TweetComposer({
  onTweetCreated,
}: TweetComposerProps) {
  const [text, setText] = useState("");
  const [photo, setPhoto] =
    useState<File | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  const fileInputRef =
    useRef<HTMLInputElement>(null);

  const handleSubmit = async () => {
    if (!text.trim()) {
      return;
    }

    setLoading(true);
    setError("");

    try {
      const formData = new FormData();

      formData.append(
        "text",
        text.trim()
      );

      if (photo) {
        formData.append(
          "photo",
          photo
        );
      }

      const token =
        localStorage.getItem(
          "access_token"
        );

      const response = await fetch(
        "http://localhost:8000/tweets/",
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
          },
          body: formData,
        }
      );

      if (!response.ok) {
        const data =
          await response.json();

        throw new Error(
          data.detail ||
            "Failed to create ripple"
        );
      }

      setText("");
      setPhoto(null);

      onTweetCreated();
    } catch (err: any) {
      setError(
        err.message ||
          "Something went wrong."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="composer">
      <div className="composer-avatar">
        R
      </div>

      <div className="composer-content">
        <textarea
          placeholder="What's creating a ripple?"
          value={text}
          maxLength={280}
          onChange={(e) =>
            setText(e.target.value)
          }
        />

        {error && (
          <p className="composer-error">
            {error}
          </p>
        )}

        {photo && (
          <div className="selected-image">
            <span>{photo.name}</span>

            <button
              onClick={() =>
                setPhoto(null)
              }
            >
              <X size={16} />
            </button>
          </div>
        )}

        <div className="composer-footer">
          <div className="composer-tools">
            <button
              className="image-button"
              onClick={() =>
                fileInputRef.current?.click()
              }
              type="button"
            >
              <Image size={20} />
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/png,image/jpeg,image/webp"
              hidden
              onChange={(e) =>
                setPhoto(
                  e.target.files?.[0] ||
                    null
                )
              }
            />

            <span
              className={
                text.length > 250
                  ? "character-count warning"
                  : "character-count"
              }
            >
              {text.length}/280
            </span>
          </div>

          <button
            className="ripple-button"
            disabled={
              !text.trim() || loading
            }
            onClick={handleSubmit}
          >
            <Send size={17} />

            {loading
              ? "Posting..."
              : "Ripple"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default TweetComposer;