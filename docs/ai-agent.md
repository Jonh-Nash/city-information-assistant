# AI Agent 設計

```mermaid
graph TB
    %% User Interaction
    U[ユーザ] -->|質問| AG[AIエージェント]

    %% Planning
    AG --> Plan[プラン生成Node]
    Plan --> DetermineCity{対象都市は確定？}

    %% City determination
    DetermineCity -- Yes --> GatherInfo[都市情報取得Node]
    DetermineCity -- No --> AskCity[/都市名を質問/]
    AskCity --> DetermineCity

    %% Information retrieval
    GatherInfo --> Tools[情報取得取得Tools]
    Tools --> GatherInfo

    %% Answer generation
    GatherInfo --> Compose[回答生成Node]
    Compose --> Response[ユーザへ回答]

    %% Response
    Response --> U
```
