from typing import List, Dict, Any, Annotated
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages
from .llm_interface import LLMInterface
from .tool_interface import ToolInterface

# LangGraphのState定義
class State(TypedDict):
    """チャットAgentの状態管理"""
    messages: Annotated[List[BaseMessage], add_messages]

class ChatAgent:
    """LangGraphを使用したシンプルなチャットエージェント"""
    
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
        """LangGraphのワークフローを構築"""
        # StateGraphを作成
        graph_builder = StateGraph(State)
        
        # ノードを追加
        graph_builder.add_node("chatbot", self._chatbot_node)
        graph_builder.add_node("tools", ToolNode(self.langchain_tools))
        
        # エッジを設定
        graph_builder.add_edge(START, "chatbot")
        graph_builder.add_conditional_edges(
            "chatbot",
            self._should_continue,
            {
                "tools": "tools",
                "end": END,
            }
        )
        graph_builder.add_edge("tools", "chatbot")
        
        return graph_builder.compile()
    
    def _chatbot_node(self, state: State) -> Dict[str, List[BaseMessage]]:
        """チャットボットのメインノード"""
        try:
            # システムメッセージを追加（最初のメッセージでない場合のみ）
            messages = state["messages"]
            if not messages or not isinstance(messages[0], SystemMessage):
                # 利用可能なツールの説明を動的に生成
                tool_descriptions = []
                for tool in self.tool_interfaces:
                    tool_descriptions.append(f"- {tool.name}: {tool.description}")
                
                tools_info = "\n".join(tool_descriptions) if tool_descriptions else "利用可能なツールはありません。"
                
                system_message = SystemMessage(
                    content=f"あなたは親切で有能な日本語AIアシスタントです。"
                    f"ユーザーの質問に丁寧に答え、必要に応じて利用可能なツールを使用してください。\n\n"
                    f"利用可能なツール:\n{tools_info}"
                )
                messages = [system_message] + messages
            
            # LLMを呼び出し
            response = self.llm_with_tools.invoke(messages)
            return {"messages": [response]}
            
        except Exception as e:
            print(f"Error in chatbot node: {e}")
            error_message = AIMessage(
                content="申し訳ございませんが、エラーが発生しました。"
            )
            return {"messages": [error_message]}
    
    def _should_continue(self, state: State) -> str:
        """ツールを使用するかどうかを判定"""
        messages = state["messages"]
        if not messages:
            return "end"
        
        last_message = messages[-1]
        # ツールコールがある場合はツールを実行
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "tools"
        return "end"
    
    async def chat(self, message: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """
        チャット処理のメインエントリーポイント
        
        Args:
            message: ユーザーからのメッセージ
            conversation_history: 会話履歴
            
        Returns:
            AIからの応答
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
            
            # グラフを実行
            result = await self.graph.ainvoke({"messages": messages})
            
            # 最後のメッセージを取得
            if result and "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    return last_message.content
            
            return "申し訳ございませんが、応答を生成できませんでした。"
            
        except Exception as e:
            print(f"Error in chat: {e}")
            return "申し訳ございませんが、エラーが発生しました。"
