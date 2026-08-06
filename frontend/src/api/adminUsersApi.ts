import {
  requestEmpty,
  requestJson,
  type HttpRequestOptions,
} from "./httpClient";
import type { PaginatedResponse } from "../types/pagination";
import type { UserRole } from "../types/user";

export { ApiError as AdminUsersApiError } from "./httpClient";
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

const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL as string;
const API_URL = (import.meta.env.VITE_ADMIN_API_URL as string | undefined)
  ?? AUTH_API_URL?.replace(/\/auth\/?$/, "");

type RequestOptions = Pick<HttpRequestOptions, "method" | "headers" | "body">;

function getRequestOptions(options: RequestOptions): HttpRequestOptions {
  const headers = new Headers({
    "Content-Type": "application/json",
  });

  if (options.headers) {
    new Headers(options.headers).forEach((value, key) => {
      headers.set(key, value);
    });
  }

  return {
    ...options,
    headers,
    requiredAuthMessage: "API URL or access token is missing.",
    fallbackErrorMessage: (status) =>
      `Admin users request failed with status ${status}`,
    parseErrorBody: true,
    useDetailAsMessage: true,
  };
}

async function authorizedRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  if (!API_URL) {
    throw new Error("API URL or access token is missing.");
  }

  return requestJson<T>(`${API_URL}${path}`, getRequestOptions(options));
}

async function authorizedEmptyRequest(
  path: string,
  options: RequestOptions = {},
): Promise<void> {
  if (!API_URL) {
    throw new Error("API URL or access token is missing.");
  }

  await requestEmpty(`${API_URL}${path}`, getRequestOptions(options));
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
  await authorizedEmptyRequest(`/admin/users/${userId}`, {
    method: "DELETE",
  });
}
