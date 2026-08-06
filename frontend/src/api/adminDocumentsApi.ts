import {
  requestBlob,
  requestJson,
  type HttpRequestOptions,
} from "./httpClient";
import type { PaginatedResponse } from "../types/pagination";

export { ApiError as AdminDocumentsApiError } from "./httpClient";

export interface AdminDocument {
  document_id: string;
  title: string;
  category?: string | null;
  file_type?: string | null;
  source_file_name?: string | null;
  last_updated?: string | null;
  chunk_count: number;
}

export type PaginatedAdminDocuments = PaginatedResponse<AdminDocument>;

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

export interface DocumentUpdateResponse {
  success: boolean;
  message: string;
  document_id: string;
  file_name: string;
  category: string;
  source_path: string;
}

export interface DeleteDocumentResponse {
  success: boolean;
  message: string;
  document_id: string;
}

const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL as string;
const API_URL = (import.meta.env.VITE_ADMIN_API_URL as string | undefined)
  ?? AUTH_API_URL?.replace(/\/auth\/?$/, "");

type RequestOptions = Pick<HttpRequestOptions, "method" | "headers" | "body">;

function getRequestOptions(options: RequestOptions): HttpRequestOptions {
  return {
    ...options,
    requiredAuthMessage: "API URL or access token is missing.",
    fallbackErrorMessage: (status) =>
      `Admin documents request failed with status ${status}`,
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

export function updateDocument(documentId: string, file: File) {
  const formData = new FormData();
  formData.append("file", file);

  return authorizedRequest<DocumentUpdateResponse>(
    `/admin/documents/${encodeURIComponent(documentId)}`,
    {
      method: "PUT",
      body: formData,
    },
  );
}

export function deleteAdminDocument(documentId: string) {
  return authorizedRequest<DeleteDocumentResponse>(
    `/admin/documents/${encodeURIComponent(documentId)}`,
    { method: "DELETE" },
  );
}

export async function downloadAdminDocument(documentId: string): Promise<Blob> {
  if (!API_URL) {
    throw new Error("API URL or access token is missing.");
  }

  return requestBlob(
    `${API_URL}/admin/documents/${encodeURIComponent(documentId)}/download`,
    {
      requiredAuthMessage: "API URL or access token is missing.",
      fallbackErrorMessage: (status) =>
        `Admin documents request failed with status ${status}`,
    },
  );
}
