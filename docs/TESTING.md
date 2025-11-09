# Руководство по тестированию Multi-Agent System

## Уровни тестирования

### 1. Базовое тестирование (Unit Tests)

Проверка корректности импортов и базовой функциональности:

```bash
uv run python test_graph.py
```

**Проверяет:**
- ✅ Импорт всех модулей
- ✅ Создание SessionStorage
- ✅ Создание AgentState
- ✅ Структура состояния
- ✅ Сохранение и загрузка сессий

**Ожидаемый результат:**
```
✅ ВСЕ БАЗОВЫЕ ТЕСТЫ ПРОЙДЕНЫ!
```

### 2. Интеграционное тестирование (Manual)

Для полного теста требуется:
1. Валидный API ключ в `hide_me.py`
2. Заполненный `config.json`
3. Установленный Playwright MCP

#### Шаги тестирования:

**2.1. Подготовка**

```bash
# Проверьте наличие config.json
ls -la config.json

# Проверьте наличие hide_me.py
ls -la hide_me.py

# Проверьте Playwright MCP
npx -y @playwright/mcp@latest
```

**2.2. Тест без реального браузера (Dry Run)**

Отредактируйте `main.py`, закомментируйте вызов графа:

```python
# Временно заменить:
# final_state = await graph.ainvoke(initial_state)

# На:
final_state = initial_state
final_state["applied_count"] = 0  # Симуляция
```

Запустите:
```bash
uv run python main.py
```

**Ожидаемый результат:**
- Загрузка конфигурации ✅
- Инициализация модели ✅
- Создание графа ✅
- Сохранение сессии ✅

**2.3. Полный тест с браузером**

⚠️ **Внимание**: Это реальный запуск с браузером!

```bash
uv run python main.py
```

**Что должно произойти:**
1. Запуск браузера (откроется Chrome/Firefox)
2. Переход на hh.ru
3. Логин на HeadHunter
4. Поиск вакансий
5. Генерация писем
6. Отклики на вакансии
7. Сохранение результатов

**Мониторинг в реальном времени:**

В консоли отображаются:
- 🎯 Действия Supervisor
- 📋 План от Planner
- 🌐 Действия Browser Agent
- ✍️ Генерация писем

### 3. Тестирование компонентов

#### 3.1. Тест SessionStorage

```python
from utils.storage import SessionStorage

storage = SessionStorage("data/test_sessions")
stats = storage.get_statistics()
print(stats)

# Создать тестовую сессию
test_state = {
    "session_id": "test_123",
    "user_request": "Test",
    "plan": "Test plan",
    "vacancies": [],
    "applied_count": 0,
    "start_time": 0
}

session_id = storage.save_session(test_state)
print(f"Saved: {session_id}")

# Загрузить
sessions = storage.load_recent_sessions(1)
print(f"Loaded: {len(sessions)} sessions")
```

#### 3.2. Тест config_loader

```python
from config_loader import load_config, get_resume_data, get_hh_credentials

config = load_config("config.example.json")
resume = get_resume_data(config)
login, password = get_hh_credentials(config)

print(f"Resume title: {resume.get('title')}")
print(f"Login: {login}")
```

#### 3.3. Тест создания графа

```python
from graph_agent import create_initial_state
from langchain_openai import ChatOpenAI
from hide_me import api_key

# Создать модель
model = ChatOpenAI(
    model="MiniMaxAI/MiniMax-M2",
    base_url="https://foundation-models.api.cloud.ru/v1",
    api_key=api_key,
)

# Создать состояние
state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test@test.com",
    hh_password="test",
    max_applications=1
)

print(f"State created: {state['session_id']}")
print(f"Next agent: {state['next_agent']}")
```

### 4. Проверка истории откликов

После выполнения полного теста:

```bash
# Проверить созданные сессии
ls -la data/sessions/

# Посмотреть последнюю сессию
cat data/sessions/session_*.json | tail -100
```

**Структура должна содержать:**
- session_id
- timestamp
- user_request
- plan
- vacancies_processed (массив)
- statistics

### 5. Тестирование отдельных агентов

#### 5.1. Supervisor Node

```python
from graph_agent import supervisor_node, create_initial_state

state = create_initial_state(
    user_request="Test",
    resume_data={"title": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=5
)

# Тест: нужен planner
result = supervisor_node(state)
assert result["next_agent"] == "planner"
print("✅ Supervisor routing: planner")

# Тест: достигнут лимит
state["applied_count"] = 5
result = supervisor_node(state)
assert result["next_agent"] == "end"
print("✅ Supervisor routing: end")
```

#### 5.2. Planner Node

```python
from graph_agent import planner_node, create_initial_state
from langchain_openai import ChatOpenAI
from hide_me import api_key

model = ChatOpenAI(
    model="MiniMaxAI/MiniMax-M2",
    base_url="https://foundation-models.api.cloud.ru/v1",
    api_key=api_key,
)

state = create_initial_state(
    user_request="Откликнуться на 3 вакансии",
    resume_data={"title": "Developer", "tags": ["Python"], "summary": "Test"},
    hh_login="test",
    hh_password="test",
    max_applications=3
)

result = planner_node(state, model)
print(f"✅ Plan created: {len(result['plan'])} chars")
print(f"✅ Steps: {len(result['plan_steps'])}")
```

### 6. Performance Testing

Для измерения производительности:

```python
import time
from graph_agent import create_graph, create_initial_state

start_time = time.time()

# Запустить граф
# ... код запуска ...

end_time = time.time()
execution_time = end_time - start_time

print(f"Execution time: {execution_time:.2f} seconds")
print(f"Per application: {execution_time / max_applications:.2f} seconds")
```

**Бенчмарки:**
- Создание плана: < 10 секунд
- Генерация письма: < 15 секунд
- Отклик на вакансию: < 60 секунд
- Полный цикл (5 откликов): < 10 минут

### 7. Error Handling Testing

#### 7.1. Тест без API ключа

```bash
# Переименуйте hide_me.py
mv hide_me.py hide_me.py.bak

# Запустите
uv run python main.py

# Ожидается: ImportError
```

#### 7.2. Тест без конфига

```bash
# Переименуйте config
mv config.json config.json.bak

# Запустите с использованием config_loader
python -c "from config_loader import load_config; load_config()"

# Ожидается: FileNotFoundError
```

### 8. Continuous Testing

Для регулярного тестирования создайте скрипт:

```bash
#!/bin/bash
# test_all.sh

echo "🧪 Running all tests..."

echo "\n1. Unit tests"
uv run python test_graph.py || exit 1

echo "\n2. Import tests"
python -c "from graph_agent import *; from utils.storage import *; from config_loader import *" || exit 1

echo "\n3. Config validation"
python -c "from config_loader import load_config; load_config('config.example.json')" || exit 1

echo "\n✅ All tests passed!"
```

Запуск:
```bash
chmod +x test_all.sh
./test_all.sh
```

### 9. Troubleshooting Tests

#### Тест падает на импорте LangChain

```bash
uv sync
uv pip list | grep langchain
```

#### Тест падает на Playwright MCP

```bash
npx -y @playwright/mcp@latest
```

#### Тест падает на создании директории

```bash
mkdir -p data/sessions
chmod 755 data/sessions
```

### 10. Checklist перед Production

- [ ] Все unit тесты проходят
- [ ] Config.example.json валиден
- [ ] .gitignore содержит config.json и hide_me.py
- [ ] README.md обновлен
- [ ] История сессий корректно сохраняется
- [ ] Браузер корректно запускается и закрывается
- [ ] Письма генерируются уникально
- [ ] Дубликаты вакансий фильтруются
- [ ] Логирование работает корректно
- [ ] Errors обрабатываются gracefully

---

## Быстрый тест-чек

```bash
# 1. Базовые тесты
uv run python test_graph.py

# 2. Проверка импортов
python -c "from graph_agent import *; print('✅ OK')"

# 3. Проверка config
python -c "from config_loader import load_config; load_config('config.example.json'); print('✅ OK')"

# 4. Полный запуск (если готовы)
# uv run python main.py
```

Если все 3 команды прошли успешно - система готова к работе! 🚀

