export type ChatRequest = {
  question: string;
};

export type Source = {
  document_id: string;
  title: string;
  category: string;
  chunk_index: number;
};

export type ChatResponse = {
  question: string;
  answer: string;
  sources?: Source[];
};

const API_URL = import.meta.env.VITE_RAG_API_URL as string;

export async function askQuestion(question: string): Promise<ChatResponse> {
  if (!API_URL) {
    throw new Error("VITE_RAG_API_URL is not defined.");
  }

  const response = await fetch(API_URL, {
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