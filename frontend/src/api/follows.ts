import { apiRequest } from "./client";

export interface UserSummary {
  id: number;
  username: string;
}

export interface FollowersResponse {
  username: string;
  followers_count: number;
  followers: UserSummary[];
}

export interface FollowingResponse {
  username: string;
  following_count: number;
  following: UserSummary[];
}

export async function followUser(username: string) {
  return apiRequest(`/users/${username}/follow`, {
    method: "POST",
  });
}

export async function unfollowUser(username: string) {
  return apiRequest(`/users/${username}/follow`, {
    method: "DELETE",
  });
}

export async function getFollowers(
  username: string
): Promise<FollowersResponse> {
  return apiRequest(`/users/${username}/followers`);
}

export async function getFollowing(
  username: string
): Promise<FollowingResponse> {
  return apiRequest(`/users/${username}/following`);
}