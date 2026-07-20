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
}

export type ChatResponse = {
  question: string;
  answer: string;
  sources?: Source[];
};

export type FeedbackValue = "useful" | "not_useful";

export type FeedbackRequest = {
  question: string;
  answer: string;
  feedback: FeedbackValue;
  sources?: Source[];
};

export type FeedbackResponse = {
  status: string;
  message?: string | null;
  feedback?: FeedbackValue;
};

const CHAT_API_URL = import.meta.env.VITE_RAG_API_URL as string;
const FEEDBACK_API_URL = import.meta.env.VITE_FEEDBACK_API_URL as string;

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("access_token");

  if (!token) {
    return {
      "Content-Type": "application/json",
    };
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function askQuestion(question: string): Promise<ChatResponse> {
  if (!CHAT_API_URL) {
    throw new Error("VITE_RAG_API_URL is not defined.");
  }

  const response = await fetch(CHAT_API_URL, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ question } satisfies ChatRequest),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json() as Promise<ChatResponse>;
}

export async function sendFeedback(
  feedbackRequest: FeedbackRequest
): Promise<FeedbackResponse> {
  if (!FEEDBACK_API_URL) {
    throw new Error("VITE_FEEDBACK_API_URL is not defined.");
  }

  const response = await fetch(FEEDBACK_API_URL, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(feedbackRequest),
  });

  if (!response.ok) {
    throw new Error(`Feedback request failed with status ${response.status}`);
  }

  return response.json() as Promise<FeedbackResponse>;
}