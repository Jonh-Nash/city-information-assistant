import React from "react";
import { format } from "date-fns";
import { ja } from "date-fns/locale";

interface ThinkingStep {
  id: string;
  nodeName: string;
  message: string;
  status: "processing" | "completed" | "error";
  timestamp: Date;
  data?: any;
}

interface ThinkingProcessProps {
  steps: ThinkingStep[];
  isActive: boolean;
}

const ThinkingProcess: React.FC<ThinkingProcessProps> = ({
  steps,
  isActive,
}) => {
  if (!isActive && steps.length === 0) return null;

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-4">
      <div className="flex items-center mb-3">
        <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mr-2">
          <svg
            className="w-4 h-4 text-blue-600"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
        </div>
        <h3 className="text-sm font-medium text-gray-900">
          AI思考過程
          {isActive && (
            <span className="ml-2 inline-flex items-center">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span className="ml-1 text-xs text-blue-600">処理中</span>
            </span>
          )}
        </h3>
      </div>

      <div className="space-y-2">
        {steps.map((step, index) => (
          <div key={step.id} className="flex items-start space-x-3">
            <div className="flex-shrink-0">
              {step.status === "completed" && (
                <div className="w-5 h-5 bg-green-100 rounded-full flex items-center justify-center">
                  <svg
                    className="w-3 h-3 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
              )}
              {step.status === "processing" && (
                <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
                </div>
              )}
              {step.status === "error" && (
                <div className="w-5 h-5 bg-red-100 rounded-full flex items-center justify-center">
                  <svg
                    className="w-3 h-3 text-red-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </div>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-900">{step.message}</p>
                <span className="text-xs text-gray-500">
                  {format(step.timestamp, "HH:mm:ss", { locale: ja })}
                </span>
              </div>

              {step.nodeName !== "system" && (
                <p className="text-xs text-gray-500 mt-1">
                  ノード: {step.nodeName}
                </p>
              )}

              {/* 詳細情報の表示（オプション） */}
              {step.data?.target_city && (
                <div className="mt-1 text-xs text-blue-600">
                  対象都市: {step.data.target_city}
                </div>
              )}

              {step.data?.function_calls &&
                step.data.function_calls.length > 0 && (
                  <div className="mt-1 text-xs text-purple-600">
                    ツール:{" "}
                    {step.data.function_calls
                      .map((call: any) => call.tool || "unknown")
                      .join(", ")}
                  </div>
                )}
            </div>
          </div>
        ))}
      </div>

      {/* 接続線は複雑になるため削除（シンプルな表示に変更） */}
    </div>
  );
};

export default ThinkingProcess;
