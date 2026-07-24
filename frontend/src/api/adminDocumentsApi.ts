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

export interface UploadDocumentPayload {
  title: string;
  category: string;
  file: File;
}

export interface UploadDocumentResponse {
  success: boolean;
  message: string;
  file_name: string;
  category: string;
  source_path: string;
}

export interface DeleteDocumentResponse {
  success: boolean;
  message: string;
  document_id: string;
}

export class AdminDocumentsApiError extends Error {
  status: number;
  detail?: string;

  constructor(status: number, detail?: string) {
    super(detail ?? `Admin documents request failed with status ${status}`);
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
    let detail: string | undefined;

    try {
      const errorBody = await response.json() as { detail?: unknown };
      if (typeof errorBody.detail === "string") detail = errorBody.detail;
    } catch {
      // Some error responses do not contain a JSON body.
    }

    throw new AdminDocumentsApiError(response.status, detail);
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

export function uploadAdminDocument(payload: UploadDocumentPayload) {
  const formData = new FormData();
  formData.append("title", payload.title);
  formData.append("category", payload.category);
  formData.append("file", payload.file);

  return authorizedRequest<UploadDocumentResponse>("/admin/documents/upload", {
    method: "POST",
    body: formData,
  });
}

export function deleteAdminDocument(documentId: string) {
  return authorizedRequest<DeleteDocumentResponse>(
    `/admin/documents/${encodeURIComponent(documentId)}`,
    { method: "DELETE" },
  );
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
