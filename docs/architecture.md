## レイヤ構成

- EntryPoint
  - REST API として公開
  - 外部からのリクエストを受け取り、UseCase に処理を委譲する
  - Infrastructure のインスタンスを作成
- Infrastructure
  - 外部との通信を担当 (DB・HTTP・LLM など)
  - Repository の実装
  - 各通信の DTO を定義 (InputDTO / OutputDTO)
- UseCase
  - ドメインオブジェクトのオーケストレーション
  - トランザクション境界・例外ハンドリングを担当
  - DTO と Entity の詰め替えを担当
- Domain
  - ビジネスルールを保持するエンティティ・値オブジェクト・ドメインサービス
  - Repository のインターフェースを定義

## コンポーネント一覧

### EntryPoint 層

- 外部に公開する API を定義

### Infrastructure 層

- LLM: LLM へのリクエストを実装
  - OpenAiAPI
- DB: データベースへの接続を実装
  - PostgreSQLImpl
- Tools: 外部のツールへのリクエストを実装
  - CityFactsTool
  - WeatherTool
  - TimeTool

### UseCase 層

- ChatUseCase: ユーザ入力を受け取り `ChatAgent` を呼び出す。回答を保存し DTO を返却。
- ConversationUseCase: 会話の取得・一覧・削除を行う。

### Domain 層

- Conversation / Message: 会話履歴とメッセージを表すエンティティ。
- ChatAgent: AI との対話ロジックを持つドメインサービス。LangGraph を使用してフローを制御。
- 各 Repository・Tool: 各エンティティが必要な DB・Tools のインターフェース
