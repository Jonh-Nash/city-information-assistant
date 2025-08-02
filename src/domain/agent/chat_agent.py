from typing import List, Dict, Any, Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from .llm_interface import LLMInterface
from .tool_interface import ToolInterface
import re

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
        
        # ツール実行後はツール実行済みフラグを設定してから情報取得に戻る
        graph_builder.add_edge("tools", "mark_tools_executed")
        graph_builder.add_edge("mark_tools_executed", "gather_info")
        
        # 最終回答生成後は終了
        graph_builder.add_edge("compose", END)
        
        return graph_builder.compile()
    
    def _plan_generation_node(self, state: State) -> Dict[str, Any]:
        """プラン生成Node - LLMを使用してユーザーの質問を分析し対応計画を立てる"""
        try:
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
            
            # LLMを使用してプラン生成
            system_prompt = """あなたは都市情報アシスタントのプラン生成担当です。ユーザーの質問を分析して以下の形式で応答してください：

【分析結果】
- 対象都市: [都市名または「不明」]
- 都市情報必要: [はい/いいえ]
- プラン: [対応計画の説明]

判定ルール:
1. 日本の都市名（東京、大阪、京都、名古屋、福岡、札幌、仙台、広島、神戸、北九州、千葉、横浜、さいたま、川崎、相模原、新潟、静岡、浜松、岡山、熊本、鹿児島、那覇など）が含まれているかチェック
2. 天気、気温、湿度、観光、スポット、レストラン、グルメ、ホテル、交通、アクセスなどのキーワードが含まれているかチェック
3. 都市情報が必要で都市名が明確な場合：その都市の情報を取得
4. 都市情報が必要だが都市名が不明な場合：都市名を質問
5. 都市情報が不要な場合：一般的な質問として回答

必ず上記の形式で応答してください。"""

            planning_message = HumanMessage(content=f"ユーザーの質問: {user_message}")
            
            # LLMでプラン生成
            plan_response = self.llm.invoke([SystemMessage(content=system_prompt), planning_message])
            plan_content = plan_response.content if hasattr(plan_response, 'content') else str(plan_response)
            
            # LLMの応答から情報を抽出
            target_city = self._extract_city_from_plan(plan_content)
            needs_city_info = "都市情報必要: はい" in plan_content
            city_confirmed = target_city is not None and target_city != "不明"
            
            return {
                "original_question": user_message,
                "plan": plan_content,
                "target_city": target_city,
                "city_confirmed": city_confirmed,
                "needs_city_info": needs_city_info,
                "gathered_info": state.get("gathered_info", "")
            }
            
        except Exception as e:
            print(f"Error in plan generation node: {e}")
            return state
    
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
        try:
            question_message = AIMessage(
                content="どちらの都市の情報をお探しでしょうか？都市名を教えてください。"
            )
            return {"messages": [question_message]}
            
        except Exception as e:
            print(f"Error in ask city node: {e}")
            error_message = AIMessage(
                content="申し訳ございませんが、エラーが発生しました。"
            )
            return {"messages": [error_message]}
    
    def _gather_info_node(self, state: State) -> Dict[str, Any]:
        """都市情報取得Node - ツールを使用して情報を収集"""
        try:
            target_city = state.get("target_city")
            if not target_city:
                return state
            
            # システムメッセージを作成してツール使用を促す
            system_message = SystemMessage(
                content=f"ユーザーが「{target_city}」の情報を求めています。利用可能なツールを使用して情報を取得してください。"
            )
            
            user_request = HumanMessage(
                content=f"{target_city}の情報を取得してください"
            )
            
            # ツール付きLLMに問い合わせ
            response = self.llm_with_tools.invoke([system_message, user_request])
            
            return {
                "messages": [response],
                "gathered_info": state.get("gathered_info", "")
            }
            
        except Exception as e:
            print(f"Error in gather info node: {e}")
            return state
    
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
        """回答生成Node - LLMを使用して収集した情報を基に最終回答を生成"""
        try:
            original_question = state.get("original_question", "")
            target_city = state.get("target_city", "")
            needs_city_info = state.get("needs_city_info", False)
            plan = state.get("plan", "")
            
            # 取得した情報からツール実行結果を抽出
            gathered_info = ""
            messages = state["messages"]
            for msg in messages:
                if hasattr(msg, 'content') and msg.content:
                    # ツールの実行結果が含まれている可能性のあるメッセージを探す
                    content_str = str(msg.content)
                    if any(keyword in content_str for keyword in ["天気", "度", "湿度", "晴れ", "曇り", "雨"]):
                        gathered_info += content_str + "\n"
            
            # LLMを使用して最終回答を生成
            if needs_city_info and target_city and gathered_info:
                system_prompt = f"""あなたは親切で有能な都市情報アシスタントです。以下の情報を基に、ユーザーの質問に対して詳細で有用な回答を生成してください。

【ユーザーの質問】
{original_question}

【対象都市】
{target_city}

【取得した情報】
{gathered_info}

【プラン】
{plan}

回答の要件:
1. 取得した情報を分かりやすく整理して提示
2. ユーザーの質問に直接的に答える
3. 必要に応じて追加のアドバイスや関連情報を提供
4. 丁寧で親しみやすい口調で回答
5. 情報が不足している場合は、その旨を正直に伝える

日本語で回答してください。"""
                
                user_message = HumanMessage(content=original_question)
                response = self.llm.invoke([SystemMessage(content=system_prompt), user_message])
                return {"messages": [response]}
            
            elif needs_city_info and not target_city:
                # 都市名が不明な場合
                system_prompt = """あなたは親切で有能な都市情報アシスタントです。ユーザーが都市情報を求めているようですが、対象となる都市が明確でありません。

以下の要件で回答してください:
1. 都市名を尋ねる
2. どのような情報を提供できるかを簡潔に説明
3. 親しみやすい口調で対応

日本語で回答してください。"""
                
                user_message = HumanMessage(content=f"ユーザーの質問: {original_question}")
                response = self.llm.invoke([SystemMessage(content=system_prompt), user_message])
                return {"messages": [response]}
            
            else:
                # 一般的な質問として回答
                system_prompt = f"""あなたは親切で有能な日本語AIアシスタントです。以下のユーザーの質問に丁寧に答えてください。

【ユーザーの質問】
{original_question}

【プラン】
{plan}

回答の要件:
1. 質問の内容を正確に理解して回答
2. 分かりやすく丁寧な説明
3. 必要に応じて具体例や追加情報を提供
4. 親しみやすい口調で対応

日本語で回答してください。"""
                
                user_message = HumanMessage(content=original_question)
                response = self.llm.invoke([SystemMessage(content=system_prompt), user_message])
                return {"messages": [response]}
            
        except Exception as e:
            print(f"Error in compose answer node: {e}")
            error_message = AIMessage(
                content="申し訳ございませんが、回答の生成中にエラーが発生しました。"
            )
            return {"messages": [error_message]}
    
    def _extract_city_from_text(self, text: str) -> Optional[str]:
        """テキストから都市名を抽出"""
        # 日本の主要都市名パターン
        city_patterns = [
            r"東京", r"大阪", r"京都", r"名古屋", r"福岡", r"札幌", r"仙台", r"広島", 
            r"神戸", r"北九州", r"千葉", r"横浜", r"さいたま", r"川崎", r"相模原",
            r"新潟", r"静岡", r"浜松", r"岡山", r"熊本", r"鹿児島", r"那覇"
        ]
        
        for pattern in city_patterns:
            if re.search(pattern, text):
                return re.search(pattern, text).group()
        
        return None
    
    def _extract_city_from_plan(self, plan_text: str) -> Optional[str]:
        """LLMが生成したプラン文書から都市名を抽出"""
        # "対象都市: 都市名" の形式で抽出
        city_match = re.search(r"対象都市:\s*([^\s\n]+)", plan_text)
        if city_match:
            city = city_match.group(1)
            if city != "不明":
                return city
        
        # 代替: 一般的な都市名パターンで検索
        return self._extract_city_from_text(plan_text)
    
    def _needs_city_information(self, text: str) -> bool:
        """質問が都市情報を必要とするかどうかを判定"""
        city_related_keywords = [
            "天気", "気温", "湿度", "weather", "温度", "降水", "雨", "晴れ", "曇り",
            "観光", "スポット", "レストラン", "グルメ", "ホテル", "交通", "アクセス"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in city_related_keywords)
    
    async def chat(self, message: str, conversation_history: List[Dict[str, Any]] = None) -> Dict[str, str]:
        """
        チャット処理のメインエントリーポイント
        
        Args:
            message: ユーザーからのメッセージ
            conversation_history: 会話履歴
            
        Returns:
            AIからの応答とthinking（プラン）を含む辞書
            {
                "response": str,  # AIの応答
                "thinking": str   # 思考過程（プラン）
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
                "tools_executed": False
            }
            
            # グラフを実行（再帰制限を設定）
            config = {"recursion_limit": 25}
            result = await self.graph.ainvoke(initial_state, config=config)
            
            # 結果からレスポンスとthinkingを取得
            response = "申し訳ございませんが、応答を生成できませんでした。"
            thinking = result.get("plan", "メッセージを処理しています...")
            
            # 最後のメッセージを取得
            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    response = last_message.content
            
            return {
                "response": response,
                "thinking": thinking
            }
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return {
                "response": "申し訳ございませんが、エラーが発生しました。",
                "thinking": "エラーが発生しました。"
            }
