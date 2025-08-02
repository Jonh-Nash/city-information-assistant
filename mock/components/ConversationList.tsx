import React from "react";
import Link from "next/link";
import { format } from "date-fns";
import { ja } from "date-fns/locale";
import { ConversationOutputDTO } from "../types/api";

interface ConversationListProps {
  conversations: ConversationOutputDTO[];
  onCreateConversation: () => void;
}

const ConversationList: React.FC<ConversationListProps> = ({
  conversations,
  onCreateConversation,
}) => {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">会話一覧</h1>
        <button
          onClick={onCreateConversation}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium"
        >
          新しい会話を開始
        </button>
      </div>

      {conversations.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-24 h-24 bg-gray-100 rounded-full mx-auto mb-4 flex items-center justify-center">
            <svg
              className="w-12 h-12 text-gray-400"
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
            まだ会話がありません
          </h3>
          <p className="text-gray-500 mb-4">
            新しい会話を開始して、AIアシスタントと対話してみましょう。
          </p>
          <button
            onClick={onCreateConversation}
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md text-sm font-medium"
          >
            最初の会話を開始
          </button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {conversations.map((conversation) => (
            <Link
              key={conversation.id}
              href={`/conversations/${conversation.id}`}
              className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-6"
            >
              <h3 className="font-semibold text-lg text-gray-900 mb-2 truncate">
                {conversation.title}
              </h3>
              <p className="text-sm text-gray-500 mb-4">
                作成:{" "}
                {format(new Date(conversation.created_at), "yyyy/MM/dd HH:mm", {
                  locale: ja,
                })}
              </p>
              <div className="text-sm text-gray-400">
                最終更新:{" "}
                {format(new Date(conversation.updated_at), "yyyy/MM/dd HH:mm", {
                  locale: ja,
                })}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};

export default ConversationList;
