import React, { useEffect, useRef } from "react";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import ReactMarkdown from "react-markdown";
import { MessageOutputDTO } from "../types/api";

interface MessageListProps {
  messages: MessageOutputDTO[];
  streamingMessage?: string;
  isLoading?: boolean;
}

const MessageList: React.FC<MessageListProps> = ({
  messages,
  streamingMessage,
  isLoading,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingMessage]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !streamingMessage && !isLoading && (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-blue-100 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg
              className="w-8 h-8 text-blue-500"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            会話を開始しましょう
          </h3>
          <p className="text-gray-500">
            下のメッセージ入力欄から質問やメッセージを送信してください。
          </p>
        </div>
      )}

      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${
            message.role === "user" ? "justify-end" : "justify-start"
          }`}
        >
          <div
            className={`max-w-md ${
              message.role === "user" ? "message-user" : "message-assistant"
            }`}
          >
            {message.role === "assistant" ? (
              <ReactMarkdown className="prose prose-sm max-w-none">
                {message.content}
              </ReactMarkdown>
            ) : (
              <p>{message.content}</p>
            )}
            <div
              className={`text-xs mt-2 ${
                message.role === "user" ? "text-blue-100" : "text-gray-500"
              }`}
            >
              {format(new Date(message.created_at), "HH:mm", { locale: ja })}
            </div>
          </div>
        </div>
      ))}

      {streamingMessage && (
        <div className="flex justify-start">
          <div className="message-assistant">
            <ReactMarkdown className="prose prose-sm max-w-none">
              {streamingMessage}
            </ReactMarkdown>
            <div className="text-xs text-gray-500 mt-2">
              <div className="loading-dots">
                <div></div>
                <div></div>
                <div></div>
              </div>
            </div>
          </div>
        </div>
      )}

      {isLoading && !streamingMessage && (
        <div className="flex justify-start">
          <div className="message-assistant">
            <div className="loading-dots">
              <div></div>
              <div></div>
              <div></div>
            </div>
          </div>
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  );
};

export default MessageList;
