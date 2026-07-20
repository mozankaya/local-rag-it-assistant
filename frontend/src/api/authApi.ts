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

  const response = await fetch(`${AUTH_API_URL}/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(loginRequest),
  });

  if (!response.ok) {
    throw new Error("Login failed.");
  }

  return response.json() as Promise<TokenResponse>;
}

export async function getCurrentUser(): Promise<CurrentUserResponse> {
  if (!AUTH_API_URL) {
    throw new Error("VITE_AUTH_API_URL is not defined.");
  }

  const token = getAccessToken();

  if (!token) {
    throw new Error("Access token not found.");
  }

  const response = await fetch(`${AUTH_API_URL}/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Current user request failed.");
  }

  return response.json() as Promise<CurrentUserResponse>;
}