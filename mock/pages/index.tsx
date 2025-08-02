import React, { useState, useEffect } from "react";
import { useRouter } from "next/router";
import Layout from "../components/Layout";
import ConversationList from "../components/ConversationList";
import ApiClient from "../utils/api";
import { ConversationOutputDTO } from "../types/api";

const HomePage: React.FC = () => {
  const [conversations, setConversations] = useState<ConversationOutputDTO[]>(
    []
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await ApiClient.getConversations();
      setConversations(data);
    } catch (err) {
      console.error("会話一覧の取得に失敗:", err);
      setError("会話一覧の取得に失敗しました。");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateConversation = async () => {
    try {
      const title = `新しい会話 ${new Date().toLocaleDateString("ja-JP")}`;
      const newConversation = await ApiClient.createConversation({ title });
      router.push(`/conversations/${newConversation.id}`);
    } catch (err) {
      console.error("会話の作成に失敗:", err);
      setError("会話の作成に失敗しました。");
    }
  };

  if (loading) {
    return (
      <Layout title="会話一覧 | City Information Assistant">
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

  return (
    <Layout title="会話一覧 | City Information Assistant">
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
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
              <div className="mt-4">
                <button
                  onClick={loadConversations}
                  className="text-sm bg-red-100 text-red-800 px-3 py-1 rounded-md hover:bg-red-200"
                >
                  再試行
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <ConversationList
        conversations={conversations}
        onCreateConversation={handleCreateConversation}
      />
    </Layout>
  );
};

export default HomePage;
