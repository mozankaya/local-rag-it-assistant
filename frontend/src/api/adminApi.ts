import { getAccessToken } from "./authApi";
import type { PaginatedResponse } from "../types/pagination";

export interface DashboardSummary {
  total_questions: number;
  today_questions: number;
  total_feedback: number;
  useful_feedback: number;
  not_useful_feedback: number;
  no_relevant_source_count: number;
  out_of_scope_count: number;
  llm_error_count: number;
  total_users: number;
  admin_users: number;
  standard_users: number;
}

export interface ResponseTypeCount {
  response_type: string;
  count: number;
}

export interface CategoryCount {
  category: string;
  count: number;
}

export interface FeedbackSummary {
  total_feedback: number;
  useful_feedback: number;
  not_useful_feedback: number;
}

export type ServiceStatus = "healthy" | "unavailable";

export interface ServiceStatusDetail {
  status: ServiceStatus;
  message: string;
}

export interface SystemStatusResponse {
  overall_status: "healthy" | "degraded";
  services: {
    api: ServiceStatusDetail;
    database: ServiceStatusDetail;
    n8n: ServiceStatusDetail;
    ollama: ServiceStatusDetail;
  };
}

export type ReviewItemType = "feedback" | "chat_log" | (string & {});

export type ReviewReason =
  | "not_useful"
  | "no_relevant_source"
  | "llm_error"
  | (string & {});

export interface ReviewItem {
  item_type: ReviewItemType;
  item_id: number;
  review_reason: ReviewReason;
  question: string;
  answer_preview?: string | null;
  feedback?: string | null;
  response_type?: string | null;
  category?: string | null;
  section_title?: string | null;
  created_at?: string | null;
}

export type PaginatedReviewItems = PaginatedResponse<ReviewItem>;

export class AdminApiError extends Error {
  status: number;

  constructor(status: number) {
    super(`Admin request failed with status ${status}`);
    this.status = status;
  }
}

const AUTH_API_URL = import.meta.env.VITE_AUTH_API_URL as string;
const ADMIN_API_URL = (import.meta.env.VITE_ADMIN_API_URL as string | undefined)
  ?? AUTH_API_URL?.replace(/\/auth\/?$/, "");

async function adminRequest<T>(path: string): Promise<T> {
  const token = getAccessToken();

  if (!ADMIN_API_URL || !token) {
    throw new Error("Admin API URL or access token is missing.");
  }

  const response = await fetch(`${ADMIN_API_URL}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new AdminApiError(response.status);
  }

  return response.json() as Promise<T>;
}

export function getDashboardSummary() {
  return adminRequest<DashboardSummary>("/admin/dashboard/summary");
}

export function getResponseTypes() {
  return adminRequest<ResponseTypeCount[]>("/admin/dashboard/response-types");
}

export function getCategories() {
  return adminRequest<CategoryCount[]>("/admin/dashboard/categories");
}

export function getFeedbackSummary() {
  return adminRequest<FeedbackSummary>("/admin/dashboard/feedback-summary");
}

export function getReviewItems(
  limit = 10,
  offset = 0,
  reviewReason?: ReviewReason,
) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });

  if (reviewReason) {
    query.set("review_reason", reviewReason);
  }

  return adminRequest<PaginatedReviewItems>(
    `/admin/dashboard/review-items?${query.toString()}`,
  );
}

export function getSystemStatus() {
  return adminRequest<SystemStatusResponse>("/admin/system-status");
}
