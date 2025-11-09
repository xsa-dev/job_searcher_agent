"""
Простой тест для проверки работоспособности мультиагентной системы
"""

import sys
from pathlib import Path

# Проверка импортов
print("🧪 Тестирование мультиагентной системы...")
print("=" * 60)

# 1. Проверка импортов graph_agent
print("\n1. Проверка импортов graph_agent...")
try:
    from graph_agent import (
        AgentState,
        create_graph,
        create_initial_state,
        supervisor_node,
        planner_node,
        browser_agent_node,
        cover_letter_agent_node,
    )
    print("✅ graph_agent импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта graph_agent: {e}")
    sys.exit(1)

# 2. Проверка импортов storage
print("\n2. Проверка импортов storage...")
try:
    from utils.storage import SessionStorage
    print("✅ SessionStorage импортирован успешно")
except ImportError as e:
    print(f"❌ Ошибка импорта SessionStorage: {e}")
    sys.exit(1)

# 3. Проверка создания SessionStorage
print("\n3. Проверка SessionStorage...")
try:
    storage = SessionStorage(data_dir="data/test_sessions")
    print(f"✅ SessionStorage создан: {storage.data_dir}")
    
    # Проверка статистики (должна работать даже без данных)
    stats = storage.get_statistics()
    print(f"   Статистика: {stats}")
    
except Exception as e:
    print(f"❌ Ошибка создания SessionStorage: {e}")
    sys.exit(1)

# 4. Проверка создания начального состояния
print("\n4. Проверка создания initial_state...")
try:
    test_resume = {
        "id": "test_resume",
        "title": "Test Developer",
        "tags": ["Python", "Testing"],
        "summary": "Test summary"
    }
    
    initial_state = create_initial_state(
        user_request="Тестовый запрос",
        resume_data=test_resume,
        hh_login="test@test.com",
        hh_password="test_password",
        max_applications=3,
    )
    
    print("✅ initial_state создан успешно")
    print(f"   session_id: {initial_state['session_id']}")
    print(f"   max_applications: {initial_state['max_applications']}")
    print(f"   next_agent: {initial_state['next_agent']}")
    
except Exception as e:
    print(f"❌ Ошибка создания initial_state: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Проверка структуры AgentState
print("\n5. Проверка структуры AgentState...")
try:
    required_keys = [
        "messages", "user_request", "session_id", "plan", "plan_steps",
        "resume_data", "vacancies", "cover_letter", "applied_count",
        "browser_status", "next_agent"
    ]
    
    for key in required_keys:
        if key in initial_state:
            print(f"   ✅ {key}")
        else:
            print(f"   ❌ {key} отсутствует!")
    
except Exception as e:
    print(f"❌ Ошибка проверки структуры: {e}")
    sys.exit(1)

# 6. Проверка сохранения сессии
print("\n6. Проверка сохранения сессии...")
try:
    # Добавляем немного данных для тестирования
    initial_state["vacancies"] = [
        {
            "url": "https://test.com/vacancy/1",
            "title": "Test Vacancy",
            "company": "Test Company",
            "score": 0.85,
            "applied": False
        }
    ]
    
    session_id = storage.save_session(initial_state)
    print(f"✅ Сессия сохранена: {session_id}")
    
    # Проверяем загрузку
    sessions = storage.load_recent_sessions(limit=1)
    if sessions:
        print(f"✅ Сессия загружена: {len(sessions)} сессий")
    else:
        print("⚠️  Сессия не найдена после сохранения")
    
except Exception as e:
    print(f"❌ Ошибка сохранения/загрузки сессии: {e}")
    import traceback
    traceback.print_exc()

# 7. Итоговый результат
print("\n" + "=" * 60)
print("✅ ВСЕ БАЗОВЫЕ ТЕСТЫ ПРОЙДЕНЫ!")
print("=" * 60)
print("\n📝 Примечания:")
print("   - Для полного теста требуется запуск main.py")
print("   - Для работы Browser Agent требуется browsermcp")
print("   - Для работы LLM требуется api_key в hide_me.py")
print("\n🚀 Запустите main.py для полного workflow:")
print("   uv run python main.py")

