import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Link from "next/link";
import Layout from "../../components/Layout";
import MessageList from "../../components/MessageList";
import MessageInput from "../../components/MessageInput";
import ApiClient from "../../utils/api";
import {
  ConversationOutputDTO,
  MessageOutputDTO,
  StreamingEvent,
} from "../../types/api";

const ConversationPage: React.FC = () => {
  const router = useRouter();
  const { id } = router.query;
  const conversationId = id as string;

  const [conversation, setConversation] =
    useState<ConversationOutputDTO | null>(null);
  const [messages, setMessages] = useState<MessageOutputDTO[]>([]);
  const [streamingMessage, setStreamingMessage] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (conversationId) {
      loadConversationData();
    }
  }, [conversationId]);

  const loadConversationData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const [conversationData, messagesData] = await Promise.all([
        ApiClient.getConversation(conversationId),
        ApiClient.getMessages(conversationId),
      ]);

      setConversation(conversationData);
      setMessages(messagesData);
    } catch (err) {
      console.error("データの取得に失敗:", err);
      setError("データの取得に失敗しました。");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!conversationId || isSending) return;

    setIsSending(true);
    setStreamingMessage("");
    setError(null);

    try {
      // ストリーミングでメッセージを送信
      await ApiClient.sendMessageStream(
        conversationId,
        { content },
        (event: StreamingEvent) => {
          if (event.event_type === "message_chunk" && event.data?.content) {
            setStreamingMessage((prev) => prev + event.data.content);
          } else if (event.event_type === "completed") {
            // ストリーミング完了時にメッセージ一覧を再読み込み
            setStreamingMessage("");
            loadConversationData();
          }
        },
        (error: Error) => {
          console.error("ストリーミングエラー:", error);
          setError("メッセージの送信に失敗しました。");
          setStreamingMessage("");
        }
      );
    } catch (err) {
      console.error("メッセージ送信に失敗:", err);
      setError("メッセージの送信に失敗しました。");
      setStreamingMessage("");
    } finally {
      setIsSending(false);
    }
  };

  if (isLoading) {
    return (
      <Layout title="読み込み中... | City Information Assistant">
        <div className="flex justify-center items-center h-64">
          <div className="loading-dots">
            <div></div>
            <div></div>
            <div></div>
          </div>
        </div>
      </Layout>
    );
  }

  if (!conversation) {
    return (
      <Layout title="会話が見つかりません | City Information Assistant">
        <div className="text-center py-12">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            会話が見つかりません
          </h1>
          <p className="text-gray-500 mb-6">
            指定された会話は存在しないか、削除された可能性があります。
          </p>
          <Link
            href="/"
            className="bg-blue-500 hover:bg-blue-600 text-white px-6 py-2 rounded-md text-sm font-medium"
          >
            会話一覧に戻る
          </Link>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`${conversation.title} | City Information Assistant`}>
      <div className="h-[calc(100vh-12rem)] flex flex-col bg-white rounded-lg shadow-sm border">
        <div className="flex items-center justify-between p-4 border-b">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              {conversation.title}
            </h1>
            <p className="text-sm text-gray-500">
              作成:{" "}
              {new Date(conversation.created_at).toLocaleDateString("ja-JP")}
            </p>
          </div>
          <Link
            href="/"
            className="text-gray-600 hover:text-gray-900 px-3 py-2 rounded-md text-sm font-medium"
          >
            ← 会話一覧に戻る
          </Link>
        </div>

        {error && (
          <div className="mx-4 mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg
                  className="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  エラーが発生しました
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  <p>{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        <MessageList
          messages={messages}
          streamingMessage={streamingMessage}
          isLoading={isSending && !streamingMessage}
        />

        <MessageInput
          onSendMessage={handleSendMessage}
          disabled={isSending}
          placeholder={
            isSending
              ? "AIが応答中です..."
              : "都市情報や旅行について質問してください..."
          }
        />
      </div>
    </Layout>
  );
};

export default ConversationPage;
