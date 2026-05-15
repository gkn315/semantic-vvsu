from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Fitness History")

# in-memory хранилище тренировок
_history: list[dict] = []


@mcp.tool()
def save_workout(date: str, exercises: str, duration: int) -> str:
    """Сохраняет тренировку. date - дата, exercises - упражнения, duration - минуты."""
    _history.append({"date": date, "exercises": exercises, "duration": duration})
    return f"Тренировка от {date} сохранена."


@mcp.tool()
def get_history() -> str:
    """Возвращает полную историю тренировок."""
    if not _history:
        return "История пуста."
    lines = [f"{w['date']}: {w['exercises']} ({w['duration']} мин)" for w in _history]
    return "\n".join(lines)


@mcp.tool()
def get_stats() -> str:
    """Возвращает статистику по тренировкам."""
    if not _history:
        return "Нет данных."
    total = len(_history)
    avg = sum(w["duration"] for w in _history) / total
    return f"Всего тренировок: {total}, среднее время: {avg:.0f} мин"


@mcp.tool()
def delete_last() -> str:
    """Удаляет последнюю запись из истории."""
    if not _history:
        return "История пуста."
    removed = _history.pop()
    return f"Удалена тренировка от {removed['date']}."


if __name__ == "__main__":
    mcp.run(transport="stdio")
