import { getAccessToken } from "./authApi";
import type { PaginatedResponse } from "../types/pagination";
import type { UserRole } from "../types/user";

export type { UserRole } from "../types/user";

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string | null;
  deactivated_at: string | null;
}

export type PaginatedAdminUsers = PaginatedResponse<AdminUser>;

export interface CreateUserRequest {
  full_name: string;
  email: string;
  password: string;
  role: UserRole;
}

export class AdminUsersApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, detail?: string) {
    super(detail ?? `Admin users request failed with status ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL as string;
const API_URL = (import.meta.env.VITE_ADMIN_API_URL as string | undefined)
  ?? AUTH_API_URL?.replace(/\/auth\/?$/, "");

async function authorizedRequest<T>(
  path: string,
  options: RequestInit = {},
  expectsJson = true,
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
    let detail: string | undefined;

    try {
      const errorBody = await response.json() as { detail?: unknown };
      if (typeof errorBody.detail === "string") detail = errorBody.detail;
    } catch {
      // Some error responses do not contain a JSON body.
    }

    throw new AdminUsersApiError(response.status, detail);
  }

  if (!expectsJson) return undefined as T;

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

export async function deleteAdminUser(userId: number): Promise<void> {
  await authorizedRequest<void>(`/admin/users/${userId}`, {
    method: "DELETE",
  }, false);
}
