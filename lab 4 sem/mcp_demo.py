import sys
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

load_dotenv()


async def main():
    client = MultiServerMCPClient(
        {
            "fitness": {
                "command": sys.executable,
                "args": ["fitness_server.py"],
                "transport": "stdio",
            }
        }
    )

    # одна сессия - один процесс - память сохраняется между вызовами
    async with client.session("fitness") as session:
        tools = await load_mcp_tools(session)
        print(f"MCP инструменты: {[t.name for t in tools]}\n")

        tool_map = {t.name: t for t in tools}

        def get_text(result) -> str:
            # извлекаем текст из ответа
            if isinstance(result, list):
                return result[0].get("text", str(result[0]))
            return str(result)

        # сохраняем тренировки
        print("=== Сохраняем тренировки ===")
        r = await tool_map["save_workout"].ainvoke({"date": "2024-05-01", "exercises": "приседания и жим", "duration": 60})
        print(get_text(r))
        r = await tool_map["save_workout"].ainvoke({"date": "2024-05-03", "exercises": "тяга и подтягивания", "duration": 45})
        print(get_text(r))
        r = await tool_map["save_workout"].ainvoke({"date": "2024-05-05", "exercises": "кардио и пресс", "duration": 30})
        print(get_text(r))

        # история
        print("\n=== История тренировок ===")
        r = await tool_map["get_history"].ainvoke({})
        print(get_text(r))

        # статистика
        print("\n=== Статистика ===")
        r = await tool_map["get_stats"].ainvoke({})
        print(get_text(r))


if __name__ == "__main__":
    asyncio.run(main())
