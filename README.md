# City Information Assistant

**AI Agent API & Application - Urban Information Assistant**

This project is a production-ready reference implementation of an AI agent-powered urban information system. Through natural conversations with users, it retrieves weather, local time, and basic information about cities worldwide to support travel planning.

This application (Web API) is deployed to [https://city-information-assistant-production.up.railway.app](https://city-information-assistant-production.up.railway.app).

If you want to use this application with frontend, please set `API_BASE_URL` to `https://city-information-assistant-production.up.railway.app` in `.env.local` and run `npm run dev` in `/mock` directory.

## Overview

City Information Assistant is an AI agent system that provides the following capabilities:

- **Current Weather Information** - Accurate meteorological data via OpenWeatherMap API
- **Local Time Information** - Precise timezone data via WorldTime API
- **City Basic Information** - Detailed city information leveraging Wikipedia API
- **Intelligent Conversation** - Context-aware multi-turn dialogue
- **Transparent Reasoning Process** - Visualization of agent's thinking process
- **Streaming Responses** - Real-time response delivery

### Demo Features

This system can handle scenarios such as:

- **Travel Planning**: "I'm planning a trip to Paris" → Comprehensive weather, time, and city information
- **Composite Tool Integration**: Automatic tool orchestration via LangGraph
- **Contextual Dialogue**: Continuous information provision with conversation understanding

## AI Agent Features

### Tool Orchestration

The system implements the following 3 core tools:

| Tool            | Function               | API Used                                                      | Implementation                                    |
| --------------- | ---------------------- | ------------------------------------------------------------- | ------------------------------------------------- |
| `WeatherTool`   | Current weather data   | [OpenWeatherMap API](https://openweathermap.org/current)      | `src/infrastructure/tool/wheather_tool_impl.py`   |
| `TimeTool`      | Local time data        | [World Time API](http://worldtimeapi.org/)                    | `src/infrastructure/tool/time_tool_impl.py`       |
| `CityFactsTool` | City basic information | [Wikipedia API](https://www.mediawiki.org/wiki/API:Main_page) | `src/infrastructure/tool/city_facts_tool_impl.py` |

### LangGraph Workflow

The AI agent operates with a structured workflow using LangGraph:

1. **Plan Generation** - Analysis of user input and execution plan formulation
2. **City Confirmation** - City name clarification when necessary
3. **Information Gathering** - Appropriate tool selection and execution
4. **Result Integration** - Integrated response generation from multiple tool results
5. **Error Handling** - Automatic retry and fallback functionality

## Setup & Execution Guide

### 1. Environment Configuration

```bash
# Set required API keys in .env file
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/city_assistant
OPENWEATHER_API_KEY="your_openweathermap_api_key"
OPENAI_API_KEY="your_openai_api_key"
```

### 2. Container Startup

```bash
# Start services with Docker Compose
docker compose up
```

### 3. Database Setup

```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Run database migration
python scripts/migrate_postgresql.py

# Rollback (if needed)
python scripts/migrate_postgresql.py --rollback
```

### 4. Frontend Startup

```bash
# Navigate to mock directory
cd mock

# Install dependencies
npm install

# Environment configuration
echo "API_BASE_URL=https://city-information-assistant-production.up.railway.app" > .env.local

# Start development server
npm run dev
```

## API Specification

### Endpoints

| Method | Endpoint                              | Description                      |
| ------ | ------------------------------------- | -------------------------------- |
| `GET`  | `/`                                   | Root endpoint                    |
| `GET`  | `/health`                             | Health check                     |
| `POST` | `/conversations`                      | Create new conversation          |
| `GET`  | `/conversations`                      | List conversations               |
| `GET`  | `/conversations/{id}`                 | Retrieve conversation details    |
| `GET`  | `/conversations/{id}/messages`        | Get message history              |
| `POST` | `/conversations/{id}/messages`        | Send message and get AI response |
| `POST` | `/conversations/{id}/messages/stream` | Stream AI response (SSE)         |

### Streaming Response

If you want to check the streaming, please check the frontend in the `/mock` directory.

### Response Example

Example of `/conversations/{id}/messages`

```json
{
  "user_message": {
    "id": "msg-1",
    "conversation_id": "conv-1",
    "content": "I want to trip to Paris",
    "role": "user",
    "created_at": "2025-08-03T06:12:12.826661"
  },
  "assistant_message": {
    "thinking": "{\n  \"target_city\": \"Paris\",\n  \"needs_city_info\": true,\n  \"city_confirmed\": true,\n  \"analysis\": \"The user wants to plan a trip to Paris and may need information regarding travel, attractions, weather, or other city-related details.\",\n  \"planned_actions\": \"I will provide information about attractions, weather, food, and travel tips for Paris to assist the user in planning their trip.\",\n  \"tools_to_use\": [\"city_facts_tool\", \"weather_tool\", \"attractions_tool\", \"food_tool\"]\n}",
    "function_calls": [
      { "tool": "get_weather", "parameters": { "city": "Paris,FR" } },
      {
        "tool": "get_local_time",
        "parameters": { "timezone": "Europe/Paris" }
      },
      { "tool": "get_city_facts", "parameters": { "city": "Paris" } }
    ],
    "response": "xxx"
  }
}
```

## Architecture

### Clean Architecture Design

```
├── EntryPoint     # REST API & External Interface
├── Infrastructure # External System Integration (DB・LLM・APIs)
├── UseCase        # Business Logic & Orchestration
└── Domain         # Entities・Domain Services・Rules
```

### Technology Stack

**Backend**

- Python 3.11+, FastAPI
- LangChain, LangGraph (AI Workflow)
- PostgreSQL (Persistence)
- AsyncIO (Asynchronous Processing)

**Frontend**

- Next.js 14, TypeScript
- Tailwind CSS
- Server-Sent Events (Streaming)

**External Services**

- OpenAI GPT-4 (Language Model)
- OpenWeatherMap API
- World Time API
- Wikipedia API

## Testing

```bash
# Run all tests
pytest -v

# Run tests with coverage
pytest --cov=src --cov-report=html

# Run specific tests only
pytest tests/test_chat_usecase.py -v
```
