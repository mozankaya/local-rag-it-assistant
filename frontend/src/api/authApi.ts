import { ApiError, requestJson } from "./httpClient";

export type LoginRequest = {
  email: string;
  password: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
};

export type CurrentUserResponse = {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_active: boolean;
};

const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL as string;

export function getAccessToken(): string | null {
  return localStorage.getItem("access_token");
}

export function saveAccessToken(token: string) {
  localStorage.setItem("access_token", token);
}

export function clearAccessToken() {
  localStorage.removeItem("access_token");
}

export async function loginUser(
  loginRequest: LoginRequest
): Promise<TokenResponse> {
  if (!AUTH_API_URL) {
    throw new Error("VITE_AUTH_API_URL is not defined.");
  }

  try {
    return await requestJson<TokenResponse>(`${AUTH_API_URL}/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(loginRequest),
      auth: "none",
      fallbackErrorMessage: () => "Login failed.",
    });
  } catch (error) {
    if (error instanceof ApiError && error.kind === "http") {
      throw new Error("Login failed.", { cause: error });
    }

    throw error;
  }
}

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  if (!AUTH_API_URL) {
    throw new Error("VITE_AUTH_API_URL is not defined.");
  }

  try {
    return await requestJson<CurrentUserResponse>(`${AUTH_API_URL}/me`, {
      method: "GET",
      auth: "required",
      requiredAuthMessage: "Access token not found.",
      fallbackErrorMessage: () => "Current user request failed.",
    });
  } catch (error) {
    if (error instanceof ApiError && error.kind === "http") {
      throw new Error("Current user request failed.", { cause: error });
    }

    throw error;
  }
}
