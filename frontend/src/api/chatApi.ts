import { ApiError, requestJson } from "./httpClient";

export { ApiError as ChatApiError };

export type ChatRequest = {
  question: string;
};

export interface Source {
  document_id?: string | null;
  title?: string | null;
  category?: string | null;
  section_title?: string | null;
  chunk_index?: number | string | null;
  source_file_name?: string | null;
  file_type?: string | null;
  score?: number | string | null;
}

export type ChatResponse = {
  chat_log_id: number | null;
  question: string;
  answer: string;
  sources?: Source[];
  response_type?: string | null;
};

export type FeedbackValue = "useful" | "not_useful";

export type FeedbackRequest = {
  chat_log_id: number;
  feedback: FeedbackValue;
};

export type FeedbackResponse = {
  status: string;
  message?: string | null;
  feedback?: FeedbackValue;
};

const CHAT_API_URL = import.meta.env.VITE_RAG_API_URL as string;
const FEEDBACK_API_URL = import.meta.env.VITE_FEEDBACK_API_URL as string;

export async function askQuestion(question: string): Promise<ChatResponse> {
  if (!CHAT_API_URL) {
    throw new Error("VITE_RAG_API_URL is not defined.");
  }

  return requestJson<ChatResponse>(CHAT_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question } satisfies ChatRequest),
    auth: "optional",
    fallbackErrorMessage: (status) =>
      `Request failed with status ${status}`,
  });
}

export async function sendFeedback(
  feedbackRequest: FeedbackRequest
): Promise<FeedbackResponse> {
  if (!FEEDBACK_API_URL) {
    throw new Error("VITE_FEEDBACK_API_URL is not defined.");
  }

  try {
    return await requestJson<FeedbackResponse>(FEEDBACK_API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(feedbackRequest),
      auth: "optional",
      fallbackErrorMessage: (status) =>
        `Feedback request failed with status ${status}`,
    });
  } catch (error) {
    if (error instanceof ApiError && error.kind === "http") {
      throw new Error(error.message, { cause: error });
    }

    throw error;
  }
}
