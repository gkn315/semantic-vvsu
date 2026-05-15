from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field
from typing import Literal

load_dotenv()

llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)


# --- Skills ---

BASE_PROMPT = """Ты - профессиональный фитнес-тренер и нутрициолог.
Помогаешь с тренировками, питанием и расчетом калорий.
Отвечай на русском языке. Давай конкретные и практичные советы."""

SKILLS: dict[str, str] = {
    "workout": """[Skill: Тренировки]
Давай конкретные планы с упражнениями, подходами и повторениями.
Учитывай уровень подготовки и цель пользователя.""",

    "nutrition": """[Skill: Питание]
Давай советы по питанию с примерами блюд и режимом приема пищи.
Объясняй роль каждого нутриента.""",

    "bju": """[Skill: Расчет БЖУ]
При расчете БЖУ уточняй цель: похудение, набор или поддержание.
Давай конкретные цифры в граммах.""",

    "motivation": """[Skill: Мотивация]
Поддерживай пользователя и отмечай его прогресс.
Используй позитивный и вдохновляющий тон.""",
}

SKILL_KEYWORDS: dict[str, list[str]] = {
    "workout":    ["тренировк", "упражнени", "качат", "мышц", "зал", "план тренировок"],
    "nutrition":  ["питани", "еда", "диет", "продукт", "меню", "рацион"],
    "bju":        ["бжу", "белк", "жир", "углевод", "калори", "ккал"],
    "motivation": ["мотива", "устал", "сложно", "не хочу", "лень"],
}


def detect_skills(query: str) -> list[str]:
    q = query.lower()
    return [skill for skill, kws in SKILL_KEYWORDS.items() if any(k in q for k in kws)]


def build_system_prompt(skills: list[str]) -> str:
    parts = [BASE_PROMPT]
    for name in skills:
        if name in SKILLS:
            parts.append(SKILLS[name])
    return "\n\n".join(parts)


# --- Схемы ---

class ToolRoute(BaseModel):
    tool: Literal["calculate_bju", "get_workout_plan", "get_nutrition_tips", "direct"]
    weight: float = Field(default=70.0, description="вес в кг")
    age: int = Field(default=25, description="возраст")
    goal: str = Field(default="поддержание", description="цель: похудение/набор/поддержание")
    level: str = Field(default="начинающий", description="уровень подготовки")
    days: int = Field(default=3, description="дней тренировок в неделю")


class AgentResponse(BaseModel):
    result: str = Field(description="ответ тренера на вопрос пользователя")
    confidence: float = Field(ge=0.0, le=1.0, description="уверенность в ответе от 0 до 1")
    reasons: list[str] = Field(description="список причин и обоснований такого ответа")
    risk_level: Literal["НИЗКИЙ", "СРЕДНИЙ", "ВЫСОКИЙ"] = Field(description="уровень риска для здоровья")
    analysis_type: list[str] = Field(description="какие skills были применены")


# --- Инструменты ---

def calculate_bju(weight: float, goal: str, age: int = 25) -> str:
    if goal == "похудение":
        calories = weight * 24 * 0.8
        protein = weight * 2.0
    elif goal == "набор":
        calories = weight * 24 * 1.2
        protein = weight * 2.2
    else:
        calories = weight * 24
        protein = weight * 1.8

    fat = calories * 0.25 / 9
    carbs = (calories - protein * 4 - fat * 9) / 4
    return (
        f"Калории: {calories:.0f} ккал | "
        f"Белки: {protein:.0f}г | "
        f"Жиры: {fat:.0f}г | "
        f"Углеводы: {carbs:.0f}г"
    )


def get_workout_plan(level: str, days: int, goal: str) -> str:
    plans = {
        "начинающий": f"3 дня: приседания 3x15, отжимания 3x10, планка 30с. Цель: {goal}.",
        "средний": f"{days} дней: жим лежа 4x8, тяга 4x8, приседания 4x10. Цель: {goal}.",
        "продвинутый": f"{days} дней: сплит по мышечным группам, базовые упражнения 5x5. Цель: {goal}.",
    }
    return plans.get(level, plans["начинающий"])


def get_nutrition_tips(goal: str) -> str:
    tips = {
        "похудение": "Дефицит 300-500 ккал, больше белка, меньше простых углеводов, 5-6 приемов пищи.",
        "набор": "Профицит 300-500 ккал, белок каждые 3 часа, углеводы до и после тренировки.",
        "поддержание": "Сбалансированное питание, следи за калоражем, не пропускай белок.",
    }
    return tips.get(goal, "Питайся разнообразно, следи за калориями и белком.")


# --- Агент ---

def ask_agent(query: str) -> AgentResponse:
    active_skills = detect_skills(query)
    system_prompt = build_system_prompt(active_skills)

    # вызов 1 - роутинг: какой инструмент нужен
    router = llm.with_structured_output(ToolRoute)
    route: ToolRoute = router.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Определи нужный инструмент для запроса: {query}"),
    ])

    # вызываем инструмент
    tool_result = ""
    if route.tool == "calculate_bju":
        tool_result = calculate_bju(route.weight, route.goal, route.age)
    elif route.tool == "get_workout_plan":
        tool_result = get_workout_plan(route.level, route.days, route.goal)
    elif route.tool == "get_nutrition_tips":
        tool_result = get_nutrition_tips(route.goal)

    context = f"Результат инструмента {route.tool}: {tool_result}" if tool_result else ""

    # вызов 2 - структурированный ответ
    structured_llm = llm.with_structured_output(AgentResponse)
    response: AgentResponse = structured_llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=(
            f"Запрос: {query}\n"
            f"{context}\n"
            f"Активные skills: {active_skills or ['базовый']}"
        )),
    ])

    return response
