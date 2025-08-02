from langgraph.graph import StateGraph, END
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from .llm_interface import LLMInterface
from .tool.wheather_tool import WeatherTool
from .value.wheater import Weather

# Stateを宣言
class State(BaseModel):
    messages: List[Dict[str, Any]] = []
    current_message: str = ""
    weather_data: Optional[Weather] = None
    response: str = ""
    need_weather: bool = False

class ChatAgent:
    """WheatherToolのみを使った最低限のAgent"""
    
    def __init__(self, llm: LLMInterface, weather_tool: WeatherTool):
        self.llm = llm
        self.weather_tool = weather_tool
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """LangGraphのワークフローを構築"""
        graph = StateGraph(State)
        
        # ノードを追加
        graph.add_node("analyze_message", self._analyze_message)
        graph.add_node("get_weather", self._get_weather)
        graph.add_node("generate_response", self._generate_response)
        
        # エッジを追加
        graph.set_entry_point("analyze_message")
        
        # 条件分岐
        graph.add_conditional_edges(
            "analyze_message",
            self._should_get_weather,
            {
                True: "get_weather",
                False: "generate_response"
            }
        )
        
        graph.add_edge("get_weather", "generate_response")
        graph.add_edge("generate_response", END)
        
        return graph.compile()
    
    async def _analyze_message(self, state: State) -> State:
        """メッセージを分析して天気情報が必要かを判断"""
        message = state.current_message.lower()
        need_weather = "天気" in message or "weather" in message
        
        return State(
            messages=state.messages,
            current_message=state.current_message,
            weather_data=state.weather_data,
            response=state.response,
            need_weather=need_weather
        )
    
    def _should_get_weather(self, state: State) -> bool:
        """天気情報が必要かを判定"""
        return state.need_weather
    
    async def _get_weather(self, state: State) -> State:
        """天気情報を取得"""
        # メッセージから都市名を抽出（簡単な実装）
        city = self._extract_city(state.current_message)
        weather_data = await self.weather_tool.execute(city)
        
        return State(
            messages=state.messages,
            current_message=state.current_message,
            weather_data=weather_data,
            response=state.response,
            need_weather=state.need_weather
        )
    
    def _extract_city(self, message: str) -> str:
        """メッセージから都市名を抽出（簡単な実装）"""
        cities = ["東京", "大阪", "京都", "名古屋", "福岡", "札幌"]
        for city in cities:
            if city in message:
                return city
        return "東京"  # デフォルト
    
    async def _generate_response(self, state: State) -> State:
        """LLMを使ってレスポンスを生成"""
        messages = state.messages + [{"role": "user", "content": state.current_message}]
        
        if state.weather_data:
            # 天気情報を含むレスポンスを生成
            weather_info = f"{state.weather_data.city}の天気は{state.weather_data.description}、気温は{state.weather_data.temperature}度、湿度は{state.weather_data.humidity}%です。"
            response = weather_info
        else:
            # 通常のレスポンスを生成
            response = await self.llm.generate_response(messages)
        
        new_messages = messages + [{"role": "assistant", "content": response}]
        
        return State(
            messages=new_messages,
            current_message=state.current_message,
            weather_data=state.weather_data,
            response=response,
            need_weather=state.need_weather
        )
    
    async def chat(self, message: str, conversation_history: List[Dict[str, Any]] = None) -> str:
        """チャット処理のメインエントリーポイント"""
        if conversation_history is None:
            conversation_history = []
        
        initial_state = State(
            messages=conversation_history,
            current_message=message,
            weather_data=None,
            response="",
            need_weather=False
        )
        
        result = await self.graph.ainvoke(initial_state)
        # LangGraphのainvokeは辞書を返すため、辞書アクセスを使用
        return result.get("response", "申し訳ございませんが、エラーが発生しました。")
