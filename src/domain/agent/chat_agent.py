from typing import List, Dict, Any, Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from .llm_interface import LLMInterface
from .tool_interface import ToolInterface, ToolResult
import re
from dataclasses import asdict

# LangGraphのState定義
class State(TypedDict):
    """チャットAgentの状態管理"""
    messages: Annotated[List[BaseMessage], add_messages]
    original_question: str  # ユーザーの元の質問
    plan: str  # 生成されたプラン
    target_city: Optional[str]  # 対象都市名
    city_confirmed: bool  # 都市が確定されているかどうか
    gathered_info: str  # 取得した情報
    needs_city_info: bool  # 都市情報が必要かどうか
    tools_executed: bool  # ツールが実行済みかどうか
    function_calls: List[Dict[str, Any]]  # 実行されたツールの情報
    retry_count: int  # リトライ回数
    tool_results: List[ToolResult]  # ツール実行結果のリスト

class ChatAgent:
    """LangGraphを使用した都市情報アシスタント"""
    
    def __init__(self, llm: LLMInterface, tools: List[ToolInterface]):
        """
        ChatAgentを初期化
        
        Args:
            llm: LangChainのChatModelインスタンス
            tools: 利用可能なツールのリスト
        """
        self.llm = llm
        self.tool_interfaces = tools
        
        # LangChainツールオブジェクトを取得
        self.langchain_tools = [tool.get_langchain_tool() for tool in tools]
        self.llm_with_tools = self.llm.bind_tools(self.langchain_tools)
        
        # LangGraphを構築
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """LangGraphのワークフローを構築（ai-agent.md設計通り）"""
        # StateGraphを作成
        graph_builder = StateGraph(State)
        
        # ノードを追加
        graph_builder.add_node("plan", self._plan_generation_node)
        graph_builder.add_node("ask_city", self._ask_city_node)
        graph_builder.add_node("gather_info", self._gather_info_node)
        graph_builder.add_node("tools", ToolNode(self.langchain_tools))
        graph_builder.add_node("check_tool_results", self._check_tool_results_node)
        graph_builder.add_node("mark_tools_executed", self._mark_tools_executed_node)
        graph_builder.add_node("compose", self._compose_answer_node)
        
        # エッジを設定
        graph_builder.add_edge(START, "plan")
        
        # プラン生成後の条件分岐
        graph_builder.add_conditional_edges(
            "plan",
            self._determine_city,
            {
                "ask_city": "ask_city",
                "gather_info": "gather_info",
                "compose": "compose",
            }
        )
        
        # 都市名質問後は終了（ユーザーの次の入力を待つ）
        graph_builder.add_edge("ask_city", END)
        
        # 情報取得後の条件分岐
        graph_builder.add_conditional_edges(
            "gather_info",
            self._should_use_tools,
            {
                "tools": "tools",
                "compose": "compose",
            }
        )
        
        # ツール実行後はエラーチェックを行う
        graph_builder.add_edge("tools", "check_tool_results")
        
        # エラーチェック後の条件分岐
        graph_builder.add_conditional_edges(
            "check_tool_results",
            self._should_retry_tools,
            {
                "retry": "gather_info",  # リトライが必要な場合
                "success": "mark_tools_executed",  # 成功した場合
            }
        )
        
        # ツール実行済みフラグを設定してから情報取得に戻る
        graph_builder.add_edge("mark_tools_executed", "gather_info")
        
        # 最終回答生成後は終了
        graph_builder.add_edge("compose", END)
        
        return graph_builder.compile()
    
    def _plan_generation_node(self, state: State) -> Dict[str, Any]:
        """プラン生成Node - LLMに質問分析を委ねる"""
        messages = state["messages"]
        if not messages:
            return state
        
        # 最新のユーザーメッセージを取得
        user_message = None
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_message = msg.content
                break
        
        if not user_message:
            return state
        
        # LLMに分析を全て委ねる
        system_prompt = """あなたは都市情報アシスタントです。ユーザーの質問を分析して以下のJSON形式で回答してください:

{
  "target_city": "都市名または不明",
  "needs_city_info": true/false,
  "city_confirmed": true/false,
  "analysis": "簡潔な分析内容"
}

日本の都市に関する天気・観光・グルメなどの質問の場合、needs_city_infoをtrueにしてください。
都市名が明確に含まれている場合、city_confirmedをtrueにしてください。"""

        planning_message = HumanMessage(content=user_message)
        plan_response = self.llm.invoke([SystemMessage(content=system_prompt), planning_message])
        plan_content = plan_response.content if hasattr(plan_response, 'content') else str(plan_response)
        
        # JSONから値を抽出（LLMの出力をそのまま信頼）
        target_city = self._extract_json_value(plan_content, "target_city")
        needs_city_info = "true" in str(self._extract_json_value(plan_content, "needs_city_info")).lower()
        city_confirmed = "true" in str(self._extract_json_value(plan_content, "city_confirmed")).lower()
        
        return {
            "original_question": user_message,
            "plan": plan_content,
            "target_city": target_city if target_city != "不明" else None,
            "city_confirmed": city_confirmed,
            "needs_city_info": needs_city_info,
            "gathered_info": state.get("gathered_info", ""),
            "function_calls": state.get("function_calls", [])
        }
    
    def _determine_city(self, state: State) -> str:
        """対象都市が確定しているかどうかを判定"""
        needs_city_info = state.get("needs_city_info", False)
        city_confirmed = state.get("city_confirmed", False)
        
        if needs_city_info and not city_confirmed:
            return "ask_city"
        elif needs_city_info and city_confirmed:
            return "gather_info"
        else:
            return "compose"
    
    def _ask_city_node(self, state: State) -> Dict[str, List[BaseMessage]]:
        """都市名を質問するNode"""
        question_message = AIMessage(
            content="どちらの都市の情報をお探しでしょうか？都市名を教えてください。"
        )
        return {"messages": [question_message]}
    
    def _gather_info_node(self, state: State) -> Dict[str, Any]:
        """都市情報取得Node - ツールを使用して情報を収集"""
        target_city = state.get("target_city")
        if not target_city:
            return state
        
        retry_count = state.get("retry_count", 0)
        tool_results = state.get("tool_results", [])
        
        # 最後のツール結果からエラー情報を取得
        last_failed_result = None
        for result in reversed(tool_results):
            # ToolResultオブジェクトか辞書かを判定
            success = result.success if hasattr(result, 'success') else result.get('success', True)
            if not success:
                last_failed_result = result
                break
        
        # リトライ時はエラー情報を考慮したプロンプトを作成
        if last_failed_result and retry_count > 0:
            error_message = last_failed_result.error_message if hasattr(last_failed_result, 'error_message') else str(last_failed_result.get('error_message', ''))
            
            system_prompt = f"""「{target_city}」の情報を取得してください。
前回のツール実行でエラーが発生しました：{error_message}

エラーメッセージに従って都市名の形式を調整してください。
- 日本語の都市名（例：「東京」）の場合は英語形式（例：「Tokyo,JP」）で試してください
- 都市名のスペルを確認し、必要に応じて国コードを追加してください
利用可能なツールを適切に選んで使用してください。"""
            user_content = f"{target_city}の情報を再取得してください（リトライ {retry_count}回目）"
        else:
            system_prompt = f"""「{target_city}」の情報を取得してください。利用可能なツールを適切に選んで使用してください。"""
            user_content = f"{target_city}の情報を取得してください"
        
        user_request = HumanMessage(content=user_content)
        
        # ツール付きLLMに問い合わせ
        response = self.llm_with_tools.invoke([SystemMessage(content=system_prompt), user_request])
        
        # ツール呼び出し情報を記録
        function_calls = list(state.get("function_calls", []))
        for tool_call in response.tool_calls:
            if isinstance(tool_call, dict):
                # 辞書形式の場合
                tool_name = tool_call.get("name", "unknown")
                tool_args = tool_call.get("args", {})
            else:
                # オブジェクト形式の場合
                tool_name = getattr(tool_call, "name", None) or getattr(tool_call, "function", {}).get("name", "unknown")
                tool_args = getattr(tool_call, "args", None) or getattr(tool_call, "function", {}).get("arguments", {})
            
            function_call_info = {
                "tool": tool_name,
                "parameters": tool_args
            }
            
            # 重複チェック
            if not any(
                fc.get("tool") == function_call_info["tool"] and 
                fc.get("parameters") == function_call_info["parameters"] 
                for fc in function_calls
            ):
                function_calls.append(function_call_info)
        
        # リトライ時はカウントを更新
        updated_retry_count = retry_count + 1 if last_failed_result else retry_count
        
        return {
            "messages": [response],
            "gathered_info": state.get("gathered_info", ""),
            "function_calls": function_calls,
            "retry_count": updated_retry_count
        }
    
    def _check_tool_results_node(self, state: State) -> Dict[str, Any]:
        """ツール実行結果をチェックしてToolResultオブジェクトを作成"""
        messages = state["messages"]
        tool_results = list(state.get("tool_results", []))
        
        # TODO: ここでツールの実行Resultから解析するようにしたい
        # 最新のToolMessageからツール実行結果を取得
        for msg in reversed(messages):
            if isinstance(msg, ToolMessage) and hasattr(msg, 'content') and msg.content:
                content_str = str(msg.content)
                
                # エラーインジケータをチェック
                error_indicators = ["error", "エラー", "not found", "見つかりません", "failed", "失敗"]
                is_error = any(indicator.lower() in content_str.lower() for indicator in error_indicators)
                
                if is_error:
                    # エラーの種類を判定
                    error_type = "retryable"
                    if "not found" in content_str.lower() or "見つかりません" in content_str.lower():
                        error_type = "retryable"  # 都市名の問題は修正可能
                    elif "invalid" in content_str.lower() or "unauthorized" in content_str.lower():
                        error_type = "non-retryable"
                    
                    tool_result = ToolResult(
                        success=False,
                        error_message=content_str,
                        error_type=error_type
                    )
                else:
                    # 成功として扱う
                    tool_result = ToolResult(
                        success=True,
                        data=content_str
                    )
                
                tool_results.append(tool_result)
                break
        
        return {"tool_results": tool_results}
    
    def _should_retry_tools(self, state: State) -> str:
        """リトライが必要かどうかを判定"""
        max_retries = 2
        retry_count = state.get("retry_count", 0)
        tool_results = state.get("tool_results", [])
        
        # 最新のツール結果を取得
        last_result = tool_results[-1] if tool_results else None
        
        # ツール結果がないか成功していれば成功
        if not last_result:
            return "success"
        
        # ToolResultオブジェクトか辞書かを判定
        success = last_result.success if hasattr(last_result, 'success') else last_result.get('success', True)
        if success:
            return "success"
        
        # リトライ上限に達していれば成功として扱う
        if retry_count >= max_retries:
            return "success"
        
        # エラーがありリトライ可能な場合はリトライ
        error_type = last_result.error_type if hasattr(last_result, 'error_type') else last_result.get('error_type', 'non-retryable')
        if error_type == "retryable":
            return "retry"
        else:
            return "success"  # リトライ不可能なエラーは成功として扱う
    
    def _mark_tools_executed_node(self, state: State) -> Dict[str, bool]:
        """ツール実行済みフラグを設定するNode"""
        return {"tools_executed": True}
    
    def _should_use_tools(self, state: State) -> str:
        """ツールを使用するかどうかを判定"""
        # 既にツールが実行済みの場合は回答生成に移行
        if state.get("tools_executed", False):
            return "compose"
        
        messages = state["messages"]
        if not messages:
            return "compose"
        
        last_message = messages[-1]
        # ツールコールがある場合はツールを実行
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return "compose"
    
    def _compose_answer_node(self, state: State) -> Dict[str, List[BaseMessage]]:
        """回答生成Node - LLMに回答生成を委ねる"""
        # ツール実行結果があるかチェック
        tool_results = state.get("tool_results", [])
        successful_results = []
        
        for result in tool_results:
            # ToolResultオブジェクトか辞書かを判定
            if isinstance(result, dict):
                if result.get("success", False):
                    successful_results.append(result)
            else:
                # ToolResultオブジェクトの場合
                if getattr(result, "success", False):
                    successful_results.append(result)
        
        # TODO: 複数ツールに対応する必要がある
        if successful_results:
            # 成功したツール実行結果がある場合、それを使って回答生成
            latest_result = successful_results[-1]  # 最新の成功結果を使用
            
            # データを取得（辞書かオブジェクトかに応じて）
            if isinstance(latest_result, dict):
                data = latest_result.get("data", "")
            else:
                data = getattr(latest_result, "data", "")
            
            system_prompt = f"""あなたは親切で有能な都市情報アシスタントです。
ユーザーの質問に対して、以下のツール実行結果を使って自然で有用な回答を日本語で生成してください。

ツール実行結果:
{data}

この情報を分かりやすく整理して、日本語で回答してください。
温度は摂氏で表示し、天気の説明は日本語に翻訳してください。"""
            
        else:
            # ツール実行結果がない場合の通常の回答生成
            system_prompt = """あなたは親切で有能な都市情報アシスタントです。
会話の文脈を理解して、ユーザーの質問に対して自然で有用な回答を日本語で生成してください。
ツールから取得した情報がある場合は、それを適切に解釈して分かりやすく提示してください。"""
        
        # 基本的なメッセージクリーンアップ
        messages = [SystemMessage(content=system_prompt)]
        for msg in state["messages"]:
            if isinstance(msg, (HumanMessage, AIMessage)):
                if hasattr(msg, 'content') and msg.content:
                    messages.append(msg)
        
        # LLMに回答生成を委ねる
        response = self.llm.invoke(messages)
        return {"messages": [response]}
    
    def _extract_json_value(self, text: str, key: str) -> Optional[str]:
        """JSONテキストから値を抽出"""
        import json
        try:
            # JSON全体をパース
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                json_data = json.loads(json_match.group())
                return json_data.get(key)
        except:
            # JSONパースに失敗した場合は正規表現で抽出
            pattern = rf'"{key}"\s*:\s*"?([^",\n]+)"?'
            match = re.search(pattern, text)
            return match.group(1).strip() if match else None
        return None
    
    async def chat(self, message: str, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        チャット処理のメインエントリーポイント
        
        Args:
            message: ユーザーからのメッセージ
            conversation_history: 会話履歴
            
        Returns:
            AIからの応答、thinking（プラン）、実行されたツール情報を含む辞書
            {
                "response": str,  # AIの応答
                "thinking": str,  # 思考過程（プラン）
                "function_calls": List[Dict[str, Any]]  # 実行されたツール情報
            }
        """
        try:
            # 会話履歴をLangChainのメッセージ形式に変換
            messages = []
            if conversation_history:
                for msg in conversation_history[-5:]:  # ToDo: 長い場合は圧縮するなどの処理を追加
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # 現在のユーザーメッセージを追加
            messages.append(HumanMessage(content=message))
            
            # 初期状態を設定
            initial_state = {
                "messages": messages,
                "original_question": "",
                "plan": "",
                "target_city": None,
                "city_confirmed": False,
                "gathered_info": "",
                "needs_city_info": False,
                "tools_executed": False,
                "function_calls": [],
                "retry_count": 0,
                "tool_results": []
            }
            
            # グラフを実行（再帰制限を設定）
            config = {"recursion_limit": 25}
            result = await self.graph.ainvoke(initial_state, config=config)
            
            # 結果からレスポンス、thinking、function_callsを取得
            response = "申し訳ございませんが、応答を生成できませんでした。"
            thinking = result.get("plan", "メッセージを処理しています...")
            function_calls = result.get("function_calls", [])
            
            # 最後のメッセージを取得
            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
            
            return {
                "response": response,
                "thinking": thinking,
                "function_calls": function_calls
            }
            
        except Exception as e:
            return {
                "response": "申し訳ございませんが、エラーが発生しました。",
                "thinking": "エラーが発生しました。",
                "function_calls": []
            }

    async def chat_stream(self, message: str, conversation_history: List[Dict[str, Any]] = None):
        """
        ストリーミング対応のチャット処理（SSE向け）
        
        Args:
            message: ユーザーからのメッセージ
            conversation_history: 会話履歴
            
        Yields:
            各ノードの実行結果を含む辞書
            {
                "event_type": str,  # "node_start", "node_complete", "final_response"
                "node_name": str,   # 実行中のノード名
                "status": str,      # ステータス（"processing", "completed", "error"）
                "message": str,     # ユーザー向けメッセージ
                "data": Dict[str, Any]  # ノードの実行結果
            }
        """
        try:
            # 会話履歴をLangChainのメッセージ形式に変換
            messages = []
            if conversation_history:
                for msg in conversation_history[-5:]:
                    if msg["role"] == "user":
                        messages.append(HumanMessage(content=msg["content"]))
                    elif msg["role"] == "assistant":
                        messages.append(AIMessage(content=msg["content"]))
            
            # 現在のユーザーメッセージを追加
            messages.append(HumanMessage(content=message))
            
            # 初期状態を設定
            initial_state = {
                "messages": messages,
                "original_question": "",
                "plan": "",
                "target_city": None,
                "city_confirmed": False,
                "gathered_info": "",
                "needs_city_info": False,
                "tools_executed": False,
                "function_calls": [],
                "retry_count": 0,
                "tool_results": []
            }
            
            # 処理開始を通知
            yield {
                "event_type": "processing_start",
                "node_name": "system",
                "status": "processing",
                "message": "メッセージを分析中です...",
                "data": {}
            }
            
            # グラフをストリーミング実行
            config = {"recursion_limit": 25}
            final_result = None
            
            async for chunk in self.graph.astream(initial_state, config=config):
                if not chunk:
                    continue
                
                # ノード名と結果を取得
                node_name = list(chunk.keys())[0] if chunk else "unknown"
                node_result = chunk.get(node_name, {})
                
                # ノードごとの処理状況を日本語でメッセージ化
                user_message = self._get_node_message(node_name, node_result)
                
                # ノード実行完了を通知
                yield {
                    "event_type": "node_complete", 
                    "node_name": node_name,
                    "status": "completed",
                    "message": user_message,
                    "data": {
                        "result": self._serialize_node_result(node_result),
                        "plan": node_result.get("plan", ""),
                        "target_city": node_result.get("target_city", ""),
                        "function_calls": node_result.get("function_calls", [])
                    }
                }
                
                # 最終結果を保存
                final_result = node_result
            
            # 最終応答を生成
            if final_result and "messages" in final_result and final_result["messages"]:
                last_message = final_result["messages"][-1]
                response = last_message.content if hasattr(last_message, 'content') else "応答を生成できませんでした。"
            else:
                response = "申し訳ございませんが、応答を生成できませんでした。"
            
            # 最終応答を送信
            yield {
                "event_type": "final_response",
                "node_name": "system",
                "status": "completed",
                "message": "回答を生成しました",
                "data": {
                    "response": response,
                    "thinking": final_result.get("plan", ""),
                    "function_calls": final_result.get("function_calls", [])
                }
            }
            
        except Exception as e:
            yield {
                "event_type": "error",
                "node_name": "system",
                "status": "error",
                "message": "申し訳ございませんが、エラーが発生しました。",
                "data": {"error": str(e)}
            }
    
    def _get_node_message(self, node_name: str, node_result: Dict[str, Any]) -> str:
        """ノードの実行状況を日本語メッセージに変換"""
        node_messages = {
            "plan": "質問を分析してプランを生成しています...",
            "ask_city": "都市名を確認しています...",
            "gather_info": "都市情報を収集しています...",
            "tools": "外部ツールを実行して情報を取得しています...",
            "check_tool_results": "ツール実行結果を確認しています...",
            "mark_tools_executed": "ツール実行を完了しました",
            "compose": "回答を生成しています..."
        }
        
        base_message = node_messages.get(node_name, f"{node_name}を実行中...")
        
        # ノード結果に基づいてより詳細な情報を追加
        if node_name == "plan" and "target_city" in node_result:
            city = node_result.get("target_city")
            if city and city != "不明":
                base_message = f"質問を分析しました。対象都市: {city}"
            else:
                base_message = "質問を分析しました。都市名の確認が必要です。"
        
        elif node_name == "gather_info" and "function_calls" in node_result:
            calls = node_result.get("function_calls", [])
            retry_count = node_result.get("retry_count", 0)
            if calls:
                tool_names = [call.get("tool", "unknown") for call in calls]
                if retry_count > 0:
                    base_message = f"ツールを使用して情報を再収集中 ({retry_count}回目): {', '.join(tool_names)}"
                else:
                    base_message = f"ツールを使用して情報を収集中: {', '.join(tool_names)}"
        
        elif node_name == "check_tool_results":
            tool_results = node_result.get("tool_results", [])
            last_result = tool_results[-1] if tool_results else None
            if last_result:
                # ToolResultオブジェクトか辞書かを判定
                success = last_result.success if hasattr(last_result, 'success') else last_result.get('success', True)
                
                if not success:
                    base_message = "ツール実行でエラーを検出しました。リトライを検討中..."
                else:
                    base_message = "ツール実行が正常に完了しました"
            else:
                base_message = "ツール実行が正常に完了しました"
        
        elif node_name == "tools" and "messages" in node_result:
            # ツール実行結果を抽出
            messages = node_result.get("messages", [])
            tool_results = []
            for msg in messages:
                if hasattr(msg, 'content') and hasattr(msg, 'type'):
                    # LangChainのToolMessageの場合
                    if hasattr(msg, 'type') and 'tool' in str(msg.type).lower():
                        tool_results.append(msg.content)
                elif isinstance(msg, dict) and msg.get("type") == "tool":
                    # シリアライズされたToolMessageの場合
                    tool_results.append(msg.get("content", ""))
            
            if tool_results:
                # ツール実行結果の概要を表示（長すぎる場合は短縮）
                result_summary = tool_results[0][:100] + ("..." if len(tool_results[0]) > 100 else "")
                base_message = f"ツール実行完了: {result_summary}"
            else:
                base_message = "ツールを実行しました"
        
        elif node_name == "compose" and "messages" in node_result:
            base_message = "最終的な回答を生成しました"
        
        return base_message
    
    def _serialize_node_result(self, node_result: Dict[str, Any]) -> Dict[str, Any]:
        """ノード結果をJSON serializableな形式に変換"""
        if not isinstance(node_result, dict):
            return {}
        
        serialized = {}
        for key, value in node_result.items():
            if key == "tool_results" and isinstance(value, list):
                # ToolResultリストを変換
                serialized[key] = []
                for tool_result in value:
                    if isinstance(tool_result, ToolResult):
                        # ToolResultオブジェクトを辞書に変換
                        serialized[key].append(asdict(tool_result))
                    else:
                        # 既に辞書形式の場合はそのまま
                        serialized[key].append(tool_result)
            elif key == "messages" and isinstance(value, list):
                # メッセージリストを変換
                serialized[key] = []
                for msg in value:
                    if hasattr(msg, 'content') and hasattr(msg, 'type'):
                        # LangChainメッセージオブジェクトの場合
                        msg_type = msg.type if hasattr(msg, 'type') else str(type(msg).__name__)
                        msg_role = getattr(msg, 'role', 'unknown')
                        
                        # ToolMessageの場合は特別な処理
                        if 'tool' in str(msg_type).lower():
                            msg_role = 'tool'
                        elif msg_type == 'ai':
                            msg_role = 'assistant'
                        elif msg_type == 'human':
                            msg_role = 'user'
                        
                        serialized[key].append({
                            "content": msg.content,
                            "type": msg_type,
                            "role": msg_role
                        })
                    else:
                        # 普通の辞書の場合
                        serialized[key].append(str(msg))
            elif hasattr(value, 'content'):
                # 単一のメッセージオブジェクトの場合
                msg_type = value.type if hasattr(value, 'type') else str(type(value).__name__)
                msg_role = getattr(value, 'role', 'unknown')
                
                # ToolMessageの場合は特別な処理
                if 'tool' in str(msg_type).lower():
                    msg_role = 'tool'
                elif msg_type == 'ai':
                    msg_role = 'assistant'
                elif msg_type == 'human':
                    msg_role = 'user'
                
                serialized[key] = {
                    "content": value.content,
                    "type": msg_type,
                    "role": msg_role
                }
            elif isinstance(value, (str, int, float, bool, list, dict, type(None))):
                # JSON serializableな基本型の場合
                serialized[key] = value
            else:
                # その他のオブジェクトは文字列に変換
                serialized[key] = str(value)
        
        return serialized