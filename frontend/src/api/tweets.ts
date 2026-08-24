import { apiRequest } from "./client";

export interface Tweet {
  id: number;
  user_id: number;
  username: string;
  text: string;
  photo: string | null;
  created_at: string;
  updated_at: string | null;
  like_count: number;
  liked_by_me: boolean;
  comment_count: number;
}

export interface TweetListResponse {
  tweets: Tweet[];
  page: number;
  limit: number;
  total: number;
  has_next: boolean;
}

export async function getTweets(
  page = 1,
  limit = 10
): Promise<TweetListResponse> {
  return apiRequest(
    `/tweets/?page=${page}&limit=${limit}`
  );
}

export async function createTweet(
  text: string,
  photo?: File
): Promise<Tweet> {
  const formData = new FormData();

  formData.append("text", text);

  if (photo) {
    formData.append("photo", photo);
  }

  return apiRequest("/tweets/", {
    method: "POST",
    body: formData,
  });
}

export async function updateTweet(
  tweetId: number,
  text: string
): Promise<Tweet> {
  return apiRequest(`/tweets/${tweetId}`, {
    method: "PUT",
    body: JSON.stringify({ text }),
  });
}

export async function deleteTweet(
  tweetId: number
): Promise<void> {
  await apiRequest(`/tweets/${tweetId}`, {
    method: "DELETE",
  });
}

export async function likeTweet(
  tweetId: number
) {
  return apiRequest(`/tweets/${tweetId}/like`, {
    method: "POST",
  });
}

export async function unlikeTweet(
  tweetId: number
) {
  return apiRequest(`/tweets/${tweetId}/like`, {
    method: "DELETE",
  });
}