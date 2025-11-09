# Тесты для мультиагентной системы

## Обзор

Набор unit-тестов для проверки всех модулей мультиагентной системы (MAS) в директории `mas/`.

## Структура тестов

### Модульные тесты (pytest)

- **test_mas_state.py** - Тесты для `mas/state.py`
  - Создание начального состояния
  - Типы и значения полей AgentState
  - История сессий и уже откликнутых вакансий

- **test_mas_supervisor_node.py** - Тесты для `mas/supervisor_node.py`
  - Маршрутизация к planner, browser_agent, cover_letter_agent
  - Условия завершения (лимит откликов, ошибки, обработка вакансий)

- **test_mas_utils.py** - Тесты для `mas/utils.py`
  - Форматирование истории
  - Парсинг планов и писем
  - Извлечение успешных писем
  - Проверка авторизации

- **test_mas_prompts.py** - Тесты для `mas/prompts.py`
  - Форматирование всех системных промптов
  - Наличие ключевых слов и маркеров

- **test_mas_tools.py** - Тесты для `mas/tools.py`
  - Функция wait_tool
  - Схема WaitInput
  - wait_tool_instance

- **test_mas_graph.py** - Тесты для `mas/graph.py`
  - Создание и компиляция графа
  - Добавление wait_tool к инструментам
  - Вызов графа

- **test_mas_init.py** - Тесты для `mas/__init__.py` и обратной совместимости
  - Импорты из mas
  - Обратная совместимость через graph_agent.py
  - Экспорты __all__

### Фикстуры (conftest.py)

- `mock_resume_data` - Тестовые данные резюме
- `mock_state` - Базовое состояние
- `mock_sessions` - История сессий
- `mock_vacancy` - Тестовая вакансия
- `mock_llm` - Мок ChatOpenAI модели
- `mock_tools` - Мок MCP инструментов

### Старые тесты (обратная совместимость)

- **test_graph.py** - Базовая проверка импортов и создания состояния
- **test_graph_detailed.py** - Детальная проверка компонентов graph_agent

## Запуск тестов

### Установка зависимостей

```bash
uv pip install pytest pytest-asyncio
```

### Запуск всех тестов mas/

```bash
cd /path/to/job_searcher_agent
PYTHONPATH=. uv run pytest tests/test_mas_*.py -v
```

### Запуск конкретного теста

```bash
PYTHONPATH=. uv run pytest tests/test_mas_state.py -v
```

### Запуск с подробным выводом

```bash
PYTHONPATH=. uv run pytest tests/test_mas_*.py -vv --tb=short
```

### Запуск старых тестов

```bash
PYTHONPATH=. uv run python tests/test_graph.py
PYTHONPATH=. uv run python tests/test_graph_detailed.py
```

## Статистика тестов

### Новые тесты (pytest)
- **60 тестов** всего
- **test_mas_state.py**: 7 тестов
- **test_mas_supervisor_node.py**: 9 тестов
- **test_mas_utils.py**: 13 тестов
- **test_mas_prompts.py**: 11 тестов
- **test_mas_tools.py**: 8 тестов
- **test_mas_graph.py**: 5 тестов
- **test_mas_init.py**: 7 тестов

### Старые тесты (обратная совместимость)
- **test_graph.py**: 6 проверок
- **test_graph_detailed.py**: ~40 проверок

## Покрытие

Тесты покрывают:
- ✅ Создание и валидация состояния
- ✅ Логика маршрутизации supervisor
- ✅ Все вспомогательные функции
- ✅ Форматирование промптов
- ✅ Инструменты (wait_tool)
- ✅ Создание графа
- ✅ Обратную совместимость с graph_agent.py
- ✅ Импорты и экспорты модуля mas

## CI/CD

Для интеграции в CI/CD добавьте в workflow:

```yaml
- name: Run tests
  run: |
    uv pip install pytest pytest-asyncio
    PYTHONPATH=. uv run pytest tests/test_mas_*.py -v
```

## Примечания

- Асинхронные тесты используют `pytest-asyncio`
- Тесты не требуют реального браузера (используются моки)
- Тесты не требуют API ключей
- Все тесты независимы и могут запускаться параллельно

