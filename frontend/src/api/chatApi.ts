export type ChatRequest = {
  question: string;
};

export interface Source {
  document_id: string;
  title: string;
  category: string;
  section_title?: string;
  chunk_index: number;
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
  message: string;
  feedback: FeedbackValue;
};

const CHAT_API_URL = import.meta.env.VITE_RAG_API_URL as string;
const FEEDBACK_API_URL = import.meta.env.VITE_FEEDBACK_API_URL as string;

export async function askQuestion(question: string): Promise<ChatResponse> {
  if (!CHAT_API_URL) {
    throw new Error("VITE_RAG_API_URL is not defined.");
  }

  const response = await fetch(CHAT_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
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
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(feedbackRequest),
  });

  if (!response.ok) {
    throw new Error(`Feedback request failed with status ${response.status}`);
  }

  return response.json() as Promise<FeedbackResponse>;
}