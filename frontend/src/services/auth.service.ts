import { api } from "../api/client";

export type AuthRequest = {
  full_name?: string;
  email: string;
  password: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
};

export async function authenticate(data: AuthRequest) {
  const response = await api.post<AuthResponse>("/api/v1/auth", data);
  return response.data;
}