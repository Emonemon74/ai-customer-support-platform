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

export type DemoSession = AuthResponse & { conversation_id: number };

export type PublicConfig = {
  demo_enabled: boolean;
  demo_max_messages: number;
  demo_ttl_hours: number;
};

export type CurrentUser = {
  id: number;
  full_name: string;
  email: string;
  is_demo: boolean;
};

export async function startDemo() {
  const response = await api.post<DemoSession>("/api/v1/auth/demo");
  return response.data;
}

export async function getPublicConfig() {
  const response = await api.get<PublicConfig>("/api/v1/config");
  return response.data;
}

export async function getCurrentUser() {
  const response = await api.get<CurrentUser>("/api/v1/users/me");
  return response.data;
}
