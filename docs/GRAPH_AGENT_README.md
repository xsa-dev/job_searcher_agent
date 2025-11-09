# Multi-Agent System для автоматизации откликов на вакансии

## Архитектура

Система построена на базе **LangGraph** и состоит из 4 агентов:

### Агенты

1. **Supervisor** 🎯
   - Главный контроллер системы
   - Анализирует текущее состояние
   - Маршрутизирует задачи между агентами
   - Принимает решение о завершении работы

2. **Planner** 📋
   - Создает детальный план работы
   - Адаптирует план на лету на основе результатов
   - Учитывает историю предыдущих сессий
   - Оптимизирует стратегию откликов

3. **Browser Agent** 🌐
   - Выполняет действия в браузере через Playwright MCP
   - Логин на HeadHunter
   - Поиск и анализ вакансий
   - Отправка откликов

4. **Cover Letter Agent** ✍️
   - Генерирует персонализированные сопроводительные письма
   - Использует Foundation Model (MiniMaxAI/MiniMax-M2)
   - Адаптирует письма под вакансию и компанию
   - Учитывает успешные примеры из истории

### Workflow

```
User Request → Supervisor → Planner (создать план)
             ↓
   Supervisor → Browser Agent (логин на HH)
             ↓
   Supervisor → Browser Agent (поиск вакансий)
             ↓
   ┌─────────────────────────────────────┐
   │ Цикл для каждой вакансии:          │
   │                                     │
   │ Supervisor → Cover Letter Agent     │
   │            → Browser Agent (отклик) │
   │            → Supervisor (продолжить?)│
   └─────────────────────────────────────┘
             ↓
        END (цель достигнута или лимит)
```

## Состояние системы (AgentState)

Состояние передается между всеми агентами и содержит:

- **messages**: история сообщений LLM
- **user_request**: запрос пользователя
- **plan**: текущий план работы
- **plan_steps**: список шагов плана
- **resume_data**: данные резюме
- **vacancies**: список найденных вакансий
- **current_vacancy**: текущая обрабатываемая вакансия
- **cover_letter**: сгенерированное письмо
- **applied_count**: количество отправленных откликов
- **browser_status**: статус браузера
- **previous_sessions**: история предыдущих сессий
- **already_applied_urls**: URLs вакансий с откликами

## Использование

### Запуск

```bash
cd /Users/alxy/Desktop/1PROJ/PrometheusAi/job_searcher_agent
uv run python main.py
```

### Настройка

Отредактируйте `main.py` для настройки:

```python
# Данные резюме
resume_data = {
    "id": "resume_001",
    "title": "Python Backend Developer",
    "tags": ["Python", "Django", "FastAPI", "PostgreSQL"],
    "summary": "Опытный Python разработчик...",
}

# Параметры запуска
initial_state = create_initial_state(
    user_request="Откликнуться на 5 вакансий Python разработчика",
    resume_data=resume_data,
    hh_login="your_email@example.com",
    hh_password="your_password",
    max_applications=5,  # лимит откликов
)
```

## История сессий

Система автоматически сохраняет все сессии в `data/sessions/`:

### Структура сессии

```json
{
  "session_id": "session_12345",
  "timestamp": "2025-11-07T10:30:00",
  "user_request": "...",
  "plan": "...",
  "resume_used": {...},
  "vacancies_processed": [
    {
      "url": "https://hh.ru/vacancy/123",
      "title": "Python Developer",
      "company": "Company Name",
      "score": 0.85,
      "cover_letter": "...",
      "applied": true,
      "applied_at": "2025-11-07T10:35:00"
    }
  ],
  "statistics": {
    "total_vacancies_found": 20,
    "total_applied": 5,
    "average_score": 0.82,
    "execution_time": 300
  }
}
```

### Использование истории

При следующем запуске система:
- Загружает последние 10 сессий
- Анализирует успешные отклики (высокие scores)
- Избегает дубликатов (проверяет URLs)
- Адаптирует стратегию на основе паттернов

## Компоненты

### graph_agent.py

Основной модуль с реализацией:
- AgentState (TypedDict)
- Узлы графа (supervisor, planner, browser_agent, cover_letter_agent)
- Системные промпты для каждого агента
- Функции создания графа

### utils/storage.py

Модуль для работы с историей:
- `SessionStorage` - класс для сохранения/загрузки сессий
- `save_session()` - сохранение сессии в JSON
- `load_recent_sessions()` - загрузка истории
- `check_vacancy_applied()` - проверка дубликатов
- `get_statistics()` - общая статистика

### main.py

Точка входа:
- Инициализация MCP клиента
- Инициализация Foundation Model
- Создание и запуск графа
- Сохранение результатов

## Адаптация планов

Planner Agent автоматически адаптирует план на основе:

1. **История успешных откликов**
   - Анализирует вакансии с высоким score
   - Выявляет паттерны успешных писем

2. **Избегание дубликатов**
   - Проверяет URLs в истории
   - Пропускает уже обработанные вакансии

3. **Оптимизация критериев поиска**
   - Использует успешные паттерны из истории
   - Корректирует search filters

## Логирование

Система предоставляет детальное логирование:

```
🎯 SUPERVISOR: Анализ текущего состояния
📋 PLANNER: Создание/адаптация плана
🌐 BROWSER AGENT: Работа с браузером
✍️ COVER LETTER AGENT: Генерация письма
```

Каждый агент логирует:
- Входные данные
- Выполняемые действия
- Результаты работы
- Ошибки (если есть)

## Расширение системы

### Добавление нового агента

1. Создайте функцию узла:
```python
def new_agent_node(state: AgentState, model: ChatOpenAI) -> AgentState:
    # логика агента
    return state
```

2. Добавьте узел в граф:
```python
workflow.add_node("new_agent", lambda state: new_agent_node(state, model))
```

3. Добавьте маршрутизацию в supervisor:
```python
workflow.add_conditional_edges(
    "supervisor",
    supervisor_router,
    {
        "new_agent": "new_agent",
        # ...
    }
)
```

### Кастомизация промптов

Все системные промпты находятся в `graph_agent.py`:
- `SUPERVISOR_PROMPT`
- `PLANNER_PROMPT`
- `BROWSER_AGENT_PROMPT`
- `COVER_LETTER_AGENT_PROMPT`

Отредактируйте их для изменения поведения агентов.

## Troubleshooting

### Браузер не запускается

```bash
# Установите Playwright MCP
npx -y @playwright/mcp@latest
```

### Ошибки Foundation Model

Проверьте:
- `api_key` в `hide_me.py`
- Доступность API: `https://foundation-models.api.cloud.ru/v1`

### История не загружается

Убедитесь, что директория существует:
```bash
mkdir -p data/sessions
```

## Performance

- Средняя скорость: ~1-2 минуты на отклик (включая генерацию письма)
- Рекомендуемый лимит: 5-10 откликов за сессию
- Размер истории: последние 50 сессий для анализа

## Roadmap

- [ ] Интеграция с Telegram для уведомлений
- [ ] Автоматическая оценка качества писем
- [ ] A/B тестирование разных стилей писем
- [ ] ML-модель для предсказания успеха отклика
- [ ] Поддержка других job boards (Habr Career, LinkedIn)

