export interface CopilotMessage {
  role: 'user' | 'assistant';
  text: string;
  timestamp?: string;
}

export interface CopilotQuery {
  query: string;
  context?: Record<string, unknown>;
}
