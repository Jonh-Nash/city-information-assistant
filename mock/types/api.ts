// API Response型定義（バックエンドのDTOに対応）

export interface ConversationOutputDTO {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageOutputDTO {
  id: string;
  conversation_id: string;
  content: string;
  role: "user" | "assistant";
  created_at: string;
}

export interface ChatResponseOutputDTO {
  thinking: string;
  function_calls: any[];
  response: string;
}

export interface MessageResponseOutputDTO {
  user_message: MessageOutputDTO;
  assistant_message: ChatResponseOutputDTO;
}

// API Request型定義
export interface ConversationCreateInputDTO {
  title: string;
}

export interface MessageInputDTO {
  content: string;
}

// ストリーミングイベント型定義
export interface StreamingEvent {
  event_type: string;
  node_name: string;
  status: string;
  message?: string;
  data?: any;
}
