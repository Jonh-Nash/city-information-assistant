import axios from "axios";
import {
  ConversationOutputDTO,
  MessageOutputDTO,
  MessageResponseOutputDTO,
  ConversationCreateInputDTO,
  MessageInputDTO,
  StreamingEvent,
} from "../types/api";

const API_BASE_URL = process.env.API_BASE_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export class ApiClient {
  // 会話一覧を取得
  static async getConversations(): Promise<ConversationOutputDTO[]> {
    const response = await api.get("/conversations");
    return response.data;
  }

  // 新しい会話を作成
  static async createConversation(
    data: ConversationCreateInputDTO
  ): Promise<ConversationOutputDTO> {
    const response = await api.post("/conversations", data);
    return response.data;
  }

  // 特定の会話を取得
  static async getConversation(
    conversationId: string
  ): Promise<ConversationOutputDTO> {
    const response = await api.get(`/conversations/${conversationId}`);
    return response.data;
  }

  // 会話のメッセージ一覧を取得
  static async getMessages(
    conversationId: string
  ): Promise<MessageOutputDTO[]> {
    const response = await api.get(`/conversations/${conversationId}/messages`);
    return response.data;
  }

  // メッセージを送信（非ストリーミング）
  static async sendMessage(
    conversationId: string,
    data: MessageInputDTO
  ): Promise<MessageResponseOutputDTO> {
    const response = await api.post(
      `/conversations/${conversationId}/messages`,
      data
    );
    return response.data;
  }

  // メッセージを送信（ストリーミング）
  static async sendMessageStream(
    conversationId: string,
    data: MessageInputDTO,
    onEvent: (event: StreamingEvent) => void,
    onError?: (error: Error) => void
  ): Promise<void> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations/${conversationId}/messages/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("Response body is not readable");
      }

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const eventData = JSON.parse(line.slice(6));
              onEvent(eventData);
            } catch (e) {
              console.error("Failed to parse SSE data:", e);
            }
          }
        }
      }
    } catch (error) {
      if (onError) {
        onError(error as Error);
      } else {
        throw error;
      }
    }
  }
}

export default ApiClient;
