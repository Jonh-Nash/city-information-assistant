import React, { useState } from "react";
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

// 特定の形式のデータを見やすく表示するヘルパー関数
const formatSpecialData = (result: any, toolName: string) => {
  // 天気情報の場合
  if (toolName === "get_weather" && result.temperature !== undefined) {
    return (
      <div className="mt-1 grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="font-medium">都市:</span> {result.city}
        </div>
        <div>
          <span className="font-medium">気温:</span> {result.temperature}°C
        </div>
        <div>
          <span className="font-medium">体感温度:</span> {result.feels_like}°C
        </div>
        <div>
          <span className="font-medium">湿度:</span> {result.humidity}%
        </div>
        <div className="col-span-2">
          <span className="font-medium">天気:</span> {result.description}
        </div>
      </div>
    );
  }

  // 時刻情報の場合
  if (toolName === "get_local_time" && result.local_time) {
    return (
      <div className="mt-1 text-xs">
        <div>
          <span className="font-medium">都市:</span> {result.city}
        </div>
        <div>
          <span className="font-medium">現地時刻:</span> {result.local_time}
        </div>
        <div>
          <span className="font-medium">タイムゾーン:</span> {result.timezone}
        </div>
      </div>
    );
  }

  // 都市情報の場合
  if (toolName === "get_city_facts" && result.population) {
    return (
      <div className="mt-1 text-xs space-y-1">
        <div>
          <span className="font-medium">都市:</span> {result.city}
        </div>
        <div>
          <span className="font-medium">人口:</span>{" "}
          {result.population?.toLocaleString()}
        </div>
        <div>
          <span className="font-medium">面積:</span> {result.area}
        </div>
        <div>
          <span className="font-medium">言語:</span>{" "}
          {result.languages?.join(", ")}
        </div>
        <div>
          <span className="font-medium">通貨:</span> {result.currency}
        </div>
        {result.famous_landmarks && (
          <div>
            <span className="font-medium">名所:</span>{" "}
            {result.famous_landmarks.join(", ")}
          </div>
        )}
      </div>
    );
  }

  return null;
};

// ツール実行結果を表示するコンポーネント
const ToolResult: React.FC<{ result: any; toolName: string }> = ({
  result,
  toolName,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!result) return null;

  // 特定の形式のデータの場合は専用表示
  const specialFormat = formatSpecialData(result, toolName);
  if (specialFormat) {
    return (
      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
        <div className="flex items-center justify-between">
          <span className="font-medium text-green-800">
            {toolName} 実行結果:
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-green-600 hover:text-green-800"
          >
            {isExpanded ? "JSON表示を隠す" : "JSON表示"}
          </button>
        </div>
        <div className="text-green-700">{specialFormat}</div>
        {isExpanded && (
          <pre className="mt-2 pt-2 border-t border-green-200 text-green-600 whitespace-pre-wrap overflow-x-auto">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  // 結果が文字列の場合
  if (typeof result === "string") {
    return (
      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
        <div className="flex items-center justify-between">
          <span className="font-medium text-green-800">
            {toolName} 実行結果:
          </span>
          {result.length > 50 && (
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-green-600 hover:text-green-800"
            >
              {isExpanded ? "折りたたむ" : "詳細表示"}
            </button>
          )}
        </div>
        <div className="mt-1 text-green-700">
          {isExpanded || result.length <= 50
            ? result
            : `${result.slice(0, 50)}...`}
        </div>
      </div>
    );
  }

  // 結果がオブジェクトの場合
  try {
    const jsonString = JSON.stringify(result, null, 2);
    return (
      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
        <div className="flex items-center justify-between">
          <span className="font-medium text-green-800">
            {toolName} 実行結果:
          </span>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-green-600 hover:text-green-800"
          >
            {isExpanded ? "折りたたむ" : "詳細表示"}
          </button>
        </div>
        {isExpanded && (
          <pre className="mt-1 text-green-700 whitespace-pre-wrap overflow-x-auto">
            {jsonString}
          </pre>
        )}
        {!isExpanded && (
          <div className="mt-1 text-green-700">
            {jsonString.length > 100
              ? `${jsonString.slice(0, 100)}...`
              : jsonString}
          </div>
        )}
      </div>
    );
  } catch (e) {
    return (
      <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-xs">
        <span className="font-medium text-green-800">{toolName} 実行結果:</span>
        <div className="mt-1 text-green-700">{String(result)}</div>
      </div>
    );
  }
};

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
                  <div className="mt-1">
                    <div className="text-xs text-purple-600 mb-1">
                      実行ツール:{" "}
                      {step.data.function_calls
                        .map((call: any) => call.tool || "unknown")
                        .join(", ")}
                    </div>
                    {/* 各ツールの実行結果を表示 */}
                    {step.data.function_calls.map(
                      (call: any, index: number) => (
                        <ToolResult
                          key={index}
                          result={call.result || call.response}
                          toolName={call.tool || "unknown"}
                        />
                      )
                    )}
                  </div>
                )}

              {/* ツール実行結果がfunction_calls以外の形式で含まれている場合 */}
              {step.data?.tool_results && (
                <div className="mt-1">
                  {Object.entries(step.data.tool_results).map(
                    ([toolName, result]) => (
                      <ToolResult
                        key={toolName}
                        result={result}
                        toolName={toolName}
                      />
                    )
                  )}
                </div>
              )}

              {/* 一般的なデータ表示（function_callsやtool_results以外） */}
              {step.data &&
                !step.data.function_calls &&
                !step.data.tool_results &&
                !step.data.target_city && (
                  <ToolResult result={step.data} toolName="実行結果" />
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
