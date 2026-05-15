import os
import json
from langchain.tools import tool
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv

load_dotenv()


# инструмент 1 - расчёт КБЖУ
@tool
def calculate_bju(weight: float, height: float, age: int, gender: str, activity: str) -> str:
    """Рассчитывает суточную норму калорий и БЖУ."""
    if gender.lower() in ("м", "m", "мужской", "male"):
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    factors = {"низкая": 1.2, "средняя": 1.55, "высокая": 1.725}
    factor = factors.get(activity.lower(), 1.375)
    tdee = round(bmr * factor)
    protein = round(weight * 1.8)
    fat = round(tdee * 0.25 / 9)
    carbs = round((tdee - protein * 4 - fat * 9) / 4)

    return (
        f"Суточная норма: {tdee} ккал\n"
        f"Белки: {protein} г | Жиры: {fat} г | Углеводы: {carbs} г"
    )


# инструмент 2 - программа тренировок
@tool
def get_workout_plan(goal: str, days_per_week: int = 3) -> str:
    """Возвращает программу тренировок по цели."""
    plans = {
        "похудение": {
            2: "Пн: кардио 40 мин + пресс. Чт: круговая (приседания, отжимания, планка).",
            3: "Пн: кардио 40 мин. Ср: силовая (приседания 4x15, выпады 3x12, планка 3x45с). Пт: кардио + пресс.",
            4: "Пн/Чт: кардио 40 мин. Вт/Пт: силовая (приседания, выпады, отжимания, планка).",
            5: "Пн-Пт: чередование кардио (30 мин) и силовых по схеме верх/низ тела.",
        },
        "набор массы": {
            2: "Пн: грудь+трицепс (жим, отжимания). Чт: спина+бицепс (тяги, подтягивания).",
            3: "Пн: ноги (приседания 4x8, жим ногами 3x10). Ср: грудь+плечи (жим лёжа 4x8). Пт: спина+руки.",
            4: "Пн: грудь. Вт: спина. Чт: ноги. Пт: плечи+руки. Акцент на базовые упражнения 4x6-8.",
            5: "Пн-Пт: сплит по группам мышц. Грудь/Спина/Ноги/Плечи/Руки. Тяжёлые базовые + изоляция.",
        },
        "поддержание": {
            2: "Пн: полное тело (приседания, отжимания, тяга). Пт: кардио 30 мин + растяжка.",
            3: "Пн: верх тела. Ср: низ тела. Пт: кардио + core.",
            4: "Пн/Ср: силовые (верх/низ). Вт/Пт: кардио по 30 мин.",
            5: "Пн-Пт: лёгкие тренировки, чередование силовых и кардио без перегрузки.",
        },
    }

    goal_key = None
    for k in plans:
        if k in goal.lower():
            goal_key = k
            break

    if not goal_key:
        return "Цель не распознана. Укажите: похудение, набор массы или поддержание."

    days = min(max(days_per_week, 2), 5)
    available = sorted(plans[goal_key].keys())
    chosen = min(available, key=lambda x: abs(x - days))
    return f"Цель: {goal_key} | Дней в неделю: {chosen}\n{plans[goal_key][chosen]}"


# инструмент 3 - советы по питанию
@tool
def get_nutrition_tips(goal: str) -> str:
    """Возвращает базовые советы по питанию для цели."""
    tips = {
        "похудение": (
            "- Дефицит калорий 300-500 ккал от нормы\n"
            "- Больше белка (яйца, куриная грудка, творог)\n"
            "- Меньше быстрых углеводов (сахар, белый хлеб)\n"
            "- 2-2.5 л воды в день"
        ),
        "набор массы": (
            "- Профицит калорий 300-500 ккал от нормы\n"
            "- Белок каждые 3-4 часа (мясо, рыба, яйца, протеин)\n"
            "- Сложные углеводы (гречка, рис, овсянка)\n"
            "- Не пропускать приёмы пищи"
        ),
        "поддержание": (
            "- Калории = норма TDEE\n"
            "- Сбалансированный рацион: белки/жиры/углеводы в пропорции 25/25/50\n"
            "- Минимум 3 полноценных приёма пищи\n"
            "- Избегать переедания в выходные"
        ),
    }
    for k, v in tips.items():
        if k in goal.lower():
            return f"Советы по питанию ({k}):\n{v}"
    return "Укажите цель: похудение, набор массы или поддержание."


tools_map = {
    "calculate_bju": calculate_bju,
    "get_workout_plan": get_workout_plan,
    "get_nutrition_tips": get_nutrition_tips,
}

SYSTEM_PROMPT = (
    "Ты - персональный фитнес-тренер. "
    "Помогаешь составить программу тренировок, рассчитать КБЖУ и дать советы по питанию. "
    'Если вопрос не связан с фитнесом, спортом или питанием - ответь строго: "Команда неизвестна". '
    "Отвечай кратко и понятно, на русском языке."
)

# промпт для определения инструмента - отвечает только JSON
ROUTER_PROMPT = """Определи какой инструмент нужен для ответа на вопрос пользователя.
Доступные инструменты:
- calculate_bju - расчёт калорий и БЖУ (нужны: weight, height, age, gender, activity)
- get_workout_plan - программа тренировок (нужны: goal, days_per_week)
- get_nutrition_tips - советы по питанию (нужен: goal)
- none - вопрос не про фитнес/спорт/питание

Ответь ТОЛЬКО валидным JSON, без пояснений:
{"tool": "название_инструмента", "args": {"параметр": "значение"}}

Примеры:
Вопрос: "рассчитай кбжу вес 70, рост 175, 25 лет, мужчина, средняя активность"
{"tool": "calculate_bju", "args": {"weight": 70, "height": 175, "age": 25, "gender": "м", "activity": "средняя"}}

Вопрос: "программа тренировок для похудения 3 раза в неделю"
{"tool": "get_workout_plan", "args": {"goal": "похудение", "days_per_week": 3}}

Вопрос: "советы по питанию для набора массы"
{"tool": "get_nutrition_tips", "args": {"goal": "набор массы"}}

Вопрос: "напиши стихотворение"
{"tool": "none", "args": {}}"""

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)


def ask(question: str) -> str:
    # шаг 1 - определяем инструмент и параметры через JSON
    router_response = llm.invoke([
        SystemMessage(content=ROUTER_PROMPT),
        HumanMessage(content=question),
    ])

    try:
        data = json.loads(router_response.content.strip())
        tool_name = data.get("tool", "none")
        args = data.get("args", {})
    except Exception:
        tool_name = "none"
        args = {}

    # шаг 2 - если вопрос не по теме - сразу возвращаем
    if tool_name == "none" or tool_name not in tools_map:
        return "Команда неизвестна"

    # шаг 3 - вызываем инструмент напрямую
    tool_result = tools_map[tool_name].invoke(args)

    # шаг 4 - финальный ответ с данными из инструмента
    final = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question),
        HumanMessage(content=f"Данные из инструмента:\n{tool_result}"),
    ])
    return final.content


if __name__ == "__main__":
    print(ask("Рассчитай мою норму калорий: вес 75кг, рост 180см, 25 лет, мужчина, средняя активность"))
    print()
    print(ask("Составь программу тренировок для похудения на 3 дня в неделю"))
    print()
    print(ask("Какие советы по питанию для набора массы?"))
    print()
    print(ask("Напиши мне рецепт борща"))
