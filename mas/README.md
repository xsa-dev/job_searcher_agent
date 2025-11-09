# MAS (Multi-Agent System) Module

Модульная структура мультиагентной системы для автоматизации откликов на вакансии HeadHunter.

## Структура модуля

```
mas/
├── __init__.py              # Экспорты основных компонентов
├── state.py                 # Определение AgentState и create_initial_state
├── prompts.py               # Системные промпты для всех агентов
├── utils.py                 # Вспомогательные функции
├── tools.py                 # wait_tool и WaitInput
├── supervisor_node.py       # Supervisor - главный контроллер
├── planner_node.py          # Planner - создание планов
├── browser_agent_node.py    # Browser Agent - работа с браузером
├── cover_letter_agent_node.py  # Cover Letter Agent - генерация писем
└── graph.py                 # Создание и компиляция графа
```

## Компоненты

### Core

#### `state.py`
- **AgentState** (TypedDict) - определение состояния системы
- **create_initial_state()** - создание начального состояния

Поля AgentState:
- Сообщения и история
- План работы и шаги
- Данные резюме и credentials
- Вакансии и отклики
- Статусы браузера
- История сессий
- Маршрутизация

#### `prompts.py`
Системные промпты для агентов:
- `SUPERVISOR_PROMPT` - промпт для маршрутизации
- `PLANNER_PROMPT` - промпт для планирования
- `BROWSER_AGENT_PROMPT` - промпт для работы с браузером
- `COVER_LETTER_AGENT_PROMPT` - промпт для генерации писем

### Nodes (Узлы графа)

#### `supervisor_node.py`
**supervisor_node(state)** - главный контроллер

Маршрутизация:
- Нет плана → `planner`
- Браузер не активен → `browser_agent`
- Есть вакансия без письма → `cover_letter_agent`
- Есть письмо → `browser_agent` (отклик)
- Достигнут лимит/ошибка → `end`

#### `planner_node.py`
**planner_node(state, model)** - создание и адаптация планов

Функции:
- Создание детального плана работы
- Переиспользование планов из истории
- Адаптация на основе предыдущих сессий

#### `browser_agent_node.py`
**browser_agent_node(state, model, tools)** - работа с браузером

Действия:
- Логин на HeadHunter
- Поиск вакансий (обычный или рекомендованные)
- Отправка откликов
- Проверка авторизации

Использует ReAct цикл с инструментами Playwright MCP:
- Playwright_navigate - навигация по URL
- playwright_get_visible_text, playwright_get_visible_html - получение содержимого
- Playwright_click, Playwright_fill - взаимодействие с элементами
- playwright_click_and_switch_tab - управление вкладками
- wait - ожидание

#### `cover_letter_agent_node.py`
**cover_letter_agent_node(state, model)** - генерация писем

Создает персонализированные сопроводительные письма:
- Анализ вакансии и резюме
- Использование примеров из истории
- Формат 500-1000 символов

### Utilities

#### `utils.py`
Вспомогательные функции:

- `_format_history_summary()` - форматирование истории сессий
- `_parse_plan()` - парсинг плана из ответа LLM
- `_parse_cover_letter()` - парсинг письма из ответа LLM
- `_get_successful_letters()` - извлечение примеров писем
- `_check_if_logged_in()` - проверка авторизации на HH
- `_get_last_unfinished_plan()` - поиск невыполненного плана

#### `tools.py`
Инструменты:

- **WaitInput** (BaseModel) - схема параметров
- **wait_tool()** - функция ожидания
- **wait_tool_instance** - StructuredTool для LangChain

### Graph

#### `graph.py`
**create_graph(mcp_tools, model)** - создание графа

Создает StateGraph с узлами:
- supervisor (точка входа)
- planner
- browser_agent
- cover_letter_agent

Условные переходы:
- От supervisor к остальным агентам
- От агентов обратно к supervisor
- Завершение через END

## Использование

### Основной импорт

```python
from mas import AgentState, create_initial_state, create_graph
```

### Создание состояния

```python
state = create_initial_state(
    user_request="Откликнуться на 5 вакансий Python разработчика",
    resume_data={
        "title": "Python Developer",
        "tags": ["Python", "Django"],
        "summary": "Опытный разработчик"
    },
    hh_login="email@example.com",
    hh_password="password",
    max_applications=5,
    use_recommended=True  # использовать рекомендованные вакансии
)
```

### Создание графа

```python
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4")
graph = create_graph(mcp_tools, model)

# Запуск
final_state = await graph.ainvoke(state)
```

## Обратная совместимость

Модуль полностью совместим со старым `graph_agent.py`:

```python
# Старый способ (через обертку)
from graph_agent import create_graph, create_initial_state, AgentState

# Новый способ (напрямую из mas)
from mas import create_graph, create_initial_state, AgentState
```

Оба способа работают идентично.

## Логирование

Каждый модуль имеет собственный logger:

```python
logger = logging.getLogger(__name__)
```

Настройка логирования в `graph_agent.py` или `main.py`.

## Архитектура

### Поток выполнения

1. **Start** → Supervisor
2. **Supervisor** → анализ состояния → маршрутизация
3. **Planner** → создание плана → Supervisor
4. **Browser Agent** → логин/поиск/отклик → Supervisor
5. **Cover Letter Agent** → генерация письма → Supervisor
6. **Supervisor** → проверка завершения → END или следующий агент

### Преимущества модульной структуры

✅ **Разделение ответственности** - каждый модуль решает свою задачу
✅ **Легкость тестирования** - unit-тесты для каждого модуля
✅ **Переиспользование кода** - импорт только нужных компонентов
✅ **Простота поддержки** - изменения локализованы в модулях
✅ **Обратная совместимость** - старый код продолжает работать

## Зависимости

```python
langchain>=1.0.4
langchain-core>=1.0.3
langchain-openai>=0.1.0
langgraph>=1.0.2
pydantic
```

## Тесты

См. `tests/README_TESTS.md` для подробной информации о тестировании.

Запуск тестов:

```bash
PYTHONPATH=. uv run pytest tests/test_mas_*.py -v
```

## Разработка

### Добавление нового узла

1. Создайте файл `mas/new_node.py`
2. Определите функцию узла:
   ```python
   async def new_node(state: AgentState, model: ChatOpenAI) -> AgentState:
       # Логика узла
       return state
   ```
3. Импортируйте в `graph.py` и добавьте в граф
4. Обновите маршрутизацию в `supervisor_node.py`
5. Создайте тесты в `tests/test_mas_new_node.py`

### Изменение промптов

Все промпты находятся в `prompts.py`. Изменяйте их там, тесты автоматически проверят форматирование.

### Добавление утилиты

Добавьте функцию в `utils.py` с префиксом `_` и создайте тесты в `tests/test_mas_utils.py`.

## Лицензия

См. основной README проекта.

