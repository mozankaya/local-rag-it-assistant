import { getAccessToken } from "./authApi";

export interface AdminDocument {
  document_id: string;
  title: string;
  category?: string | null;
  file_type?: string | null;
  source_file_name?: string | null;
  last_updated?: string | null;
  chunk_count: number;
}

export interface PaginatedAdminDocuments {
  items: AdminDocument[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface DocumentCategory {
  category: string;
  document_count: number;
}

export interface ReindexDocumentsResponse {
  success: boolean;
  message: string;
}

export class AdminDocumentsApiError extends Error {
  status: number;

  constructor(status: number) {
    super(`Admin documents request failed with status ${status}`);
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
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new AdminDocumentsApiError(response.status);
  }

  return response.json() as Promise<T>;
}

function authorizedGet<T>(path: string): Promise<T> {
  return authorizedRequest<T>(path);
}

export function getAdminDocuments(
  limit = 10,
  offset = 0,
  search = "",
  category = "",
) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (search.trim()) query.set("search", search.trim());
  if (category) query.set("category", category);

  return authorizedGet<PaginatedAdminDocuments>(
    `/admin/documents?${query.toString()}`,
  );
}

export function getDocumentCategories() {
  return authorizedGet<DocumentCategory[]>("/admin/documents/categories");
}

export function reindexAdminDocuments() {
  return authorizedRequest<ReindexDocumentsResponse>("/admin/documents/reindex", {
    method: "POST",
  });
}

export async function downloadAdminDocument(documentId: string): Promise<Blob> {
  const token = getAccessToken();

  if (!API_URL || !token) {
    throw new Error("API URL or access token is missing.");
  }

  const response = await fetch(
    `${API_URL}/admin/documents/${encodeURIComponent(documentId)}/download`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );

  if (!response.ok) {
    throw new AdminDocumentsApiError(response.status);
  }

  return response.blob();
}
