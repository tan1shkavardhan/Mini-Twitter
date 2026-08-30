import api from "./client";

export interface Tweet {
  id: number;
  user_id: number;
  username: string;
  text: string;
  photo: string | null;
  created_at: string;
  updated_at: string;
  like_count: number;
  liked_by_me: boolean;
  comment_count: number;
  hashtags: {
    id: number;
    name: string;
  }[];
  repost_count?: number;
  reposted_by_me?: boolean;
}

export interface TweetListResponse {
  tweets: Tweet[];
  page: number;
  limit: number;
  total: number;
  has_next: boolean;
}

export const getTweets = async () => {
  const response = await api.get<TweetListResponse>(
    "/tweets/?page=1&limit=20"
  );

  return response.data;
};

export const createTweet = async (
  text: string,
  photo?: File | null
) => {
  const formData = new FormData();

  formData.append("text", text);

  if (photo) {
    formData.append("photo", photo);
  }

  const response = await api.post<Tweet>(
    "/tweets/",
    formData
  );

  return response.data;
};

export const likeTweet = async (tweetId: number) => {
  const response = await api.post(
    `/tweets/${tweetId}/like`
  );

  return response.data;
};

export const unlikeTweet = async (tweetId: number) => {
  const response = await api.delete(
    `/tweets/${tweetId}/like`
  );

  return response.data;
};