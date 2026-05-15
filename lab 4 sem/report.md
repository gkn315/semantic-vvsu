# Лабораторная работа 4 - Расширение AI агента

## Что сделано

Расширен фитнес-тренер из лабы 3. Добавлены три механизма: Skills, JSON Structured Output и MCP-сервер.

## 1. JSON Structured Output

Агент возвращает не строку, а Pydantic-объект `AgentResponse`:

```python
class AgentResponse(BaseModel):
    result: str
    confidence: float          # 0.0-1.0
    reasons: list[str]
    risk_level: Literal["НИЗКИЙ", "СРЕДНИЙ", "ВЫСОКИЙ"]
    analysis_type: list[str]
```

`llm.with_structured_output(AgentResponse)` передает схему в LLM через function calling. Модель гарантированно заполняет все поля - не нужно парсить текст вручную. FastAPI эндпоинт `/ask` возвращает этот объект напрямую как JSON.

## 2. Skills - динамические мини-промпты

Базовый промпт дополняется нужными блоками в зависимости от запроса:

```
BASE_PROMPT (всегда)
  + [Skill: Тренировки]  - если в запросе про упражнения
  + [Skill: БЖУ]         - если в запросе про калории
```

Определение skills происходит по ключевым словам. Новый skill добавляется одной строкой в словарь - менять логику агента не нужно.

## 3. MCP-сервер

`fitness_server.py` - отдельный процесс с 4 инструментами для хранения истории тренировок: `save_workout`, `get_history`, `get_stats`, `delete_last`.

`langchain-mcp-adapters` автоматически оборачивает инструменты сервера в LangChain Tools. Агент получает их как обычные инструменты - без изменения своего кода.

## Стек

`langchain`, `langchain-groq`, `fastapi`, `uvicorn`, `pydantic`, `mcp`, `langchain-mcp-adapters`, `python-dotenv`

## Запуск

```bash
pip install langchain langchain-groq fastapi uvicorn mcp langchain-mcp-adapters python-dotenv

# скопировать .env.example -> .env и вставить ключ

python app.py          # FastAPI сервер на порту 8000
python mcp_demo.py     # демо MCP-сервера
```
