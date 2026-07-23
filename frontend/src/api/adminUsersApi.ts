import { getAccessToken } from "./authApi";

export type UserRole = "admin" | "user";

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string | null;
}

export interface PaginatedAdminUsers {
  items: AdminUser[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface CreateUserRequest {
  full_name: string;
  email: string;
  password: string;
  role: UserRole;
}

export class AdminUsersApiError extends Error {
  status: number;

  constructor(status: number) {
    super(`Admin users request failed with status ${status}`);
    this.status = status;
  }
}

const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL as string;
const API_URL = (import.meta.env.VITE_ADMIN_API_URL as string | undefined)
  ?? AUTH_API_URL?.replace(/\/auth\/?$/, "");

async function authorizedRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAccessToken();

  if (!API_URL || !token) {
    throw new Error("API URL or access token is missing.");
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new AdminUsersApiError(response.status);
  }

  return response.json() as Promise<T>;
}

export function getAdminUsers(limit = 10, offset = 0, search = "") {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (search.trim()) {
    query.set("search", search.trim());
  }

  return authorizedRequest<PaginatedAdminUsers>(
    `/admin/users?${query.toString()}`,
  );
}

export function createUser(payload: CreateUserRequest) {
  return authorizedRequest<AdminUser>("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateAdminUserRole(userId: number, role: UserRole) {
  return authorizedRequest<AdminUser>(`/admin/users/${userId}/role`, {
    method: "PATCH",
    body: JSON.stringify({ role }),
  });
}

export function updateAdminUserStatus(userId: number, isActive: boolean) {
  return authorizedRequest<AdminUser>(`/admin/users/${userId}/status`, {
    method: "PATCH",
    body: JSON.stringify({ is_active: isActive }),
  });
}
