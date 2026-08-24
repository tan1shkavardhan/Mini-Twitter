import { apiRequest } from "./client";

export interface Comment {
  id: number;
  user_id: number;
  username: string;
  tweet_id: number;
  text: string;
  created_at: string;
  updated_at: string | null;
}

export interface CommentListResponse {
  comments: Comment[];
  page: number;
  limit: number;
  total: number;
  has_next: boolean;
}

export async function getComments(
  tweetId: number
): Promise<CommentListResponse> {
  return apiRequest(
    `/tweets/${tweetId}/comments`
  );
}

export async function createComment(
  tweetId: number,
  text: string
): Promise<Comment> {
  return apiRequest(
    `/tweets/${tweetId}/comments`,
    {
      method: "POST",
      body: JSON.stringify({ text }),
    }
  );
}