import type { Source } from "../../api/chatApi";

export interface Message {
  id: number;
  role: "user" | "assistant";
  text: string;
  sources?: Source[];
  question?: string;
  chatLogId?: number | null;
}
