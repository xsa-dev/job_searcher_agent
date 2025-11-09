"""
Детальные unit-тесты для проверки отдельных компонентов graph_agent.py
"""

import sys
from pathlib import Path

print("🧪 Детальное тестирование компонентов graph_agent...")
print("=" * 70)

# Импорты
from graph_agent import (
    AgentState,
    create_initial_state,
    supervisor_node,
    _format_history_summary,
    _parse_plan,
    _parse_cover_letter,
    _get_successful_letters,
)

# ================================
# ТЕСТ 1: Supervisor routing logic
# ================================
print("\n1️⃣ Тест supervisor_node - логика маршрутизации")
print("-" * 70)

# 1.1. Тест: нет плана → planner
print("\n  1.1. Тест: нет плана → должен направить к planner")
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=5
)
state["plan"] = ""  # Нет плана
result = supervisor_node(state)
assert result["next_agent"] == "planner", f"Expected 'planner', got '{result['next_agent']}'"
print("     ✅ Правильно направлен к planner")

# 1.2. Тест: достигнут лимит → end
print("\n  1.2. Тест: достигнут лимит откликов → должен завершить")
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=3
)
state["applied_count"] = 3  # Достигнут лимит
result = supervisor_node(state)
assert result["next_agent"] == "end", f"Expected 'end', got '{result['next_agent']}'"
print("     ✅ Правильно завершил работу")

# 1.3. Тест: браузер не активен → browser_agent
print("\n  1.3. Тест: браузер не активен → должен направить к browser_agent")
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=5
)
state["plan"] = "Test plan"  # План есть
state["browser_session_active"] = False  # Браузер не активен
result = supervisor_node(state)
assert result["next_agent"] == "browser_agent", f"Expected 'browser_agent', got '{result['next_agent']}'"
print("     ✅ Правильно направлен к browser_agent")

# 1.4. Тест: есть вакансии без письма → cover_letter_agent
print("\n  1.4. Тест: есть вакансия без письма → должен направить к cover_letter_agent")
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=5
)
state["plan"] = "Test plan"
state["browser_session_active"] = True
state["browser_status"] = "logged_in"
state["vacancies"] = [
    {"title": "Test Vacancy", "url": "https://test.com/1"}
]
state["current_vacancy"] = state["vacancies"][0]
state["cover_letter"] = ""  # Нет письма
result = supervisor_node(state)
assert result["next_agent"] == "cover_letter_agent", f"Expected 'cover_letter_agent', got '{result['next_agent']}'"
print("     ✅ Правильно направлен к cover_letter_agent")

print("\n✅ Все тесты supervisor_node пройдены!")

# ================================
# ТЕСТ 2: Helper functions
# ================================
print("\n2️⃣ Тест helper functions")
print("-" * 70)

# 2.1. Тест _format_history_summary
print("\n  2.1. Тест _format_history_summary")
sessions = [
    {
        "timestamp": "2025-11-07T10:00:00",
        "statistics": {
            "total_vacancies_found": 10,
            "total_applied": 5,
            "average_score": 0.85
        }
    },
    {
        "timestamp": "2025-11-06T10:00:00",
        "statistics": {
            "total_vacancies_found": 8,
            "total_applied": 3,
            "average_score": 0.75
        }
    }
]
summary = _format_history_summary(sessions)
assert "Сессия" in summary, "Summary should contain 'Сессия'"
assert "0.85" in summary, "Summary should contain score 0.85"
assert "2025-11-07" in summary, "Summary should contain date"
print("     ✅ История форматируется корректно")

# Пустая история
empty_summary = _format_history_summary([])
assert empty_summary == "История отсутствует", "Empty history should return correct message"
print("     ✅ Пустая история обрабатывается корректно")

# 2.2. Тест _parse_plan
print("\n  2.2. Тест _parse_plan")
plan_text = """
PLAN:
Это детальный план работы.
Включает несколько строк.

STEPS:
1. Логин на HeadHunter
2. Поиск вакансий
3. Отправка откликов
"""
plan, steps = _parse_plan(plan_text)
assert "детальный план" in plan, "Plan should be parsed correctly"
assert len(steps) == 3, f"Expected 3 steps, got {len(steps)}"
assert "Логин на HeadHunter" in steps[0], "First step should be parsed correctly"
print(f"     ✅ План распарсен: {len(steps)} шагов")

# 2.3. Тест _parse_cover_letter
print("\n  2.3. Тест _parse_cover_letter")
letter_text = """
COVER_LETTER:
Здравствуйте!

Я хотел бы откликнуться на вашу вакансию...
"""
letter = _parse_cover_letter(letter_text)
assert "Здравствуйте" in letter, "Letter should be parsed correctly"
assert "COVER_LETTER:" not in letter, "Marker should be removed"
print("     ✅ Письмо парсится корректно")

# Текст без маркера
letter_no_marker = _parse_cover_letter("Просто текст письма")
assert letter_no_marker == "Просто текст письма", "Text without marker should be returned as-is"
print("     ✅ Текст без маркера обрабатывается корректно")

# 2.4. Тест _get_successful_letters
print("\n  2.4. Тест _get_successful_letters")
sessions_with_letters = [
    {
        "vacancies_processed": [
            {
                "title": "Python Developer",
                "applied": True,
                "score": 0.85,
                "cover_letter": "Отличное письмо для отличной вакансии..."
            },
            {
                "title": "Java Developer",
                "applied": True,
                "score": 0.6,  # Низкий score, не должно попасть
                "cover_letter": "Плохое письмо"
            }
        ]
    }
]
examples = _get_successful_letters(sessions_with_letters)
assert "Python Developer" in examples, "High-score vacancy should be in examples"
assert "Java Developer" not in examples, "Low-score vacancy should not be in examples"
assert "0.85" in examples, "Score should be in examples"
print("     ✅ Успешные письма извлекаются корректно")

# Пустые сессии
empty_examples = _get_successful_letters([])
assert empty_examples == "Примеров пока нет", "Empty sessions should return correct message"
print("     ✅ Пустые сессии обрабатываются корректно")

print("\n✅ Все тесты helper functions пройдены!")

# ================================
# ТЕСТ 3: AgentState структура
# ================================
print("\n3️⃣ Тест AgentState структуры и валидации")
print("-" * 70)

state = create_initial_state(
    user_request="Тестовый запрос",
    resume_data={
        "title": "Python Developer",
        "tags": ["Python", "Django"],
        "summary": "Опытный разработчик"
    },
    hh_login="test@test.com",
    hh_password="password123",
    max_applications=10,
    previous_sessions=[],
    already_applied_urls={"https://already-applied.com/1"}
)

# Проверяем все обязательные поля
required_fields = {
    "messages": list,
    "user_request": str,
    "session_id": str,
    "start_time": float,
    "plan": str,
    "plan_steps": list,
    "current_step": int,
    "plan_needs_update": bool,
    "resume_data": dict,
    "hh_login": str,
    "hh_password": str,
    "vacancies": list,
    "current_vacancy_index": int,
    "cover_letter": str,
    "applied_count": int,
    "max_applications": int,
    "rejected_count": int,
    "browser_status": str,
    "browser_session_active": bool,
    "previous_sessions": list,
    "already_applied_urls": set,
    "next_agent": str,
    "error_message": str,
}

print("\n  Проверка типов полей:")
for field, expected_type in required_fields.items():
    assert field in state, f"Field '{field}' is missing"
    actual_type = type(state[field])
    assert isinstance(state[field], expected_type), f"Field '{field}' has wrong type: {actual_type}, expected {expected_type}"
    print(f"     ✅ {field}: {expected_type.__name__}")

# Проверяем начальные значения
print("\n  Проверка начальных значений:")
assert state["user_request"] == "Тестовый запрос"
print(f"     ✅ user_request: '{state['user_request']}'")
assert state["max_applications"] == 10
print(f"     ✅ max_applications: {state['max_applications']}")
assert state["applied_count"] == 0
print(f"     ✅ applied_count: {state['applied_count']}")
assert state["next_agent"] == "planner"
print(f"     ✅ next_agent: '{state['next_agent']}'")
assert state["browser_session_active"] == False
print(f"     ✅ browser_session_active: {state['browser_session_active']}")
assert len(state["already_applied_urls"]) == 1
print(f"     ✅ already_applied_urls: {len(state['already_applied_urls'])} URL")

print("\n✅ Все тесты AgentState пройдены!")

# ================================
# ТЕСТ 4: Edge cases
# ================================
print("\n4️⃣ Тест edge cases и граничных условий")
print("-" * 70)

# 4.1. План с нестандартным форматом
print("\n  4.1. План без маркеров PLAN: и STEPS:")
weird_plan = "Просто план без маркеров\nНа несколько строк"
plan, steps = _parse_plan(weird_plan)
assert isinstance(plan, str), "Plan should be string"
assert isinstance(steps, list), "Steps should be list"
print("     ✅ Нестандартный формат обработан")

# 4.2. Supervisor с ошибкой браузера
print("\n  4.2. Supervisor с ошибкой браузера")
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=5
)
state["browser_status"] = "error"
state["error_message"] = "Critical browser error"
result = supervisor_node(state)
assert result["next_agent"] == "end", "Should end on browser error"
print("     ✅ Ошибка браузера обрабатывается корректно")

# 4.3. Обработка всех вакансий
print("\n  4.3. Все вакансии обработаны")
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=5
)
state["plan"] = "Test plan"
state["browser_session_active"] = True
state["vacancies"] = [
    {"title": "Vacancy 1"},
    {"title": "Vacancy 2"}
]
state["current_vacancy_index"] = 2  # Все обработаны
state["current_vacancy"] = None
result = supervisor_node(state)
assert result["next_agent"] == "end", "Should end when all vacancies processed"
print("     ✅ Завершение после обработки всех вакансий")

print("\n✅ Все edge case тесты пройдены!")

# ================================
# ИТОГОВЫЙ РЕЗУЛЬТАТ
# ================================
print("\n" + "=" * 70)
print("✅ ВСЕ ДЕТАЛЬНЫЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
print("=" * 70)
print("\n📊 Статистика:")
print("   - Тестов supervisor routing: 4")
print("   - Тестов helper functions: 7")
print("   - Тестов AgentState: 26 полей")
print("   - Тестов edge cases: 3")
print("\n   Всего проверок: ~40")
print("\n🎉 graph_agent.py работает корректно!")

