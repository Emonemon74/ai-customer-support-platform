import { api } from "../api/client";

export type RegisterRequest = {
  full_name: string;
  email: string;
  password: string;
};

export type LoginRequest = {
  email: string;
  password: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
};

export async function register(data: RegisterRequest) {
  const response = await api.post<AuthResponse>("/api/v1/auth/register", data);
  return response.data;
}

export async function login(data: LoginRequest) {
  const response = await api.post<AuthResponse>("/api/v1/auth/login", data);
  return response.data;
}
