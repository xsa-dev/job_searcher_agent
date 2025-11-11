# Job Searcher Agent - Multi-Agent System

Мультиагентная система на базе **LangGraph** для автоматизации откликов на вакансии HeadHunter с генерацией персонализированных сопроводительных писем.

## QUICK START

```
git clone что-то-там
touch .env
echo "OPENAI_API_KEY="HIDE_ME" > .env
uv run main.py
```

## 🎯 Возможности

- **4 специализированных агента**: Supervisor, Planner, Browser Agent, Cover Letter Agent
- **Адаптивное планирование**: план корректируется на лету на основе результатов
- **История откликов**: все сессии сохраняются в JSON для анализа
- **Избегание дубликатов**: автоматическая проверка уже обработанных вакансий
- **Персонализированные письма**: генерация уникальных писем для каждой вакансии
- **Цикличная работа**: обработка нескольких вакансий за один запуск

## 🏗️ Архитектура

```
┌─────────────┐
│ Supervisor  │ ◄── Главный контроллер
└──────┬──────┘
       │
   ┌───┴────┬────────┬──────────┐
   │        │        │          │
   ▼        ▼        ▼          ▼
┌─────┐ ┌──────┐ ┌───────┐ ┌────────┐
│Plan │ │Brain │ │Browser│ │ Letter │
│ner  │ │ AG   │ │ Agent │ │ Agent  │
└─────┘ └──────┘ └───────┘ └────────┘
```

### Workflow

1. **Supervisor** → **Planner** (создать план)
2. **Supervisor** → **Browser Agent** (логин на HH)
3. **Supervisor** → **Browser Agent** (поиск вакансий)
4. Цикл для каждой вакансии:
   - **Supervisor** → **Cover Letter Agent** (генерация письма)
   - **Supervisor** → **Browser Agent** (отклик)
   - **Supervisor** → (проверка: продолжить или завершить?)
5. **END**

Подробнее: [GRAPH_AGENT_README.md](./GRAPH_AGENT_README.md)

## 📦 Установка

### Требования

- Python 3.12+
- Node.js (для Playwright MCP)
- uv (менеджер пакетов)

### Шаги установки

1. **Клонировать репозиторий**

```bash
cd /Users/alxy/Desktop/1PROJ/PrometheusAi/job_searcher_agent
```

2. **Установить зависимости**

```bash
uv sync
```

3. **Установить Playwright MCP**

```bash
npx -y @playwright/mcp@latest
```

4. **Создать конфигурационный файл**

```bash
cp config.example.json config.json
```

Отредактируйте `config.json`:

```json
{
  "hh_credentials": {
    "login": "your_email@example.com",
    "password": "your_password"
  },
  "resume": {
    "title": "Python Backend Developer",
    "tags": ["Python", "Django", "FastAPI"],
    "summary": "Ваше описание..."
  },
  "search_settings": {
    "max_applications": 5
  }
}
```

5. **Создать hide_me.py с API ключом**

```python
# hide_me.py
api_key = "your_api_key_here"
```

## 🚀 Использование

### Быстрый старт

```bash
uv run python main.py
```

### Тестирование

Проверка базовой функциональности:

```bash
uv run python test_graph.py
```

### Настройка запроса

Отредактируйте `main.py`:

```python
initial_state = create_initial_state(
    user_request="Откликнуться на 5 вакансий Python разработчика в Москве",
    resume_data=resume_data,
    hh_login="your_email@example.com",
    hh_password="your_password",
    max_applications=5,  # лимит откликов за сессию
)
```

## 📊 История откликов

Все сессии автоматически сохраняются в `data/sessions/`:

```
data/
└── sessions/
    ├── session_abc123_20251107_100000.json
    ├── session_def456_20251107_110000.json
    └── ...
```

Каждая сессия содержит:
- План работы
- Список обработанных вакансий
- Сгенерированные письма
- Статистику (найдено, откликнулись, средний score)

### Использование истории

При следующем запуске система:
- Загружает последние 10 сессий
- Анализирует успешные паттерны
- Избегает дубликатов вакансий
- Адаптирует стратегию

## 🔧 Конфигурация

### config.json

Основные настройки:

- `hh_credentials` - логин и пароль для HH
- `resume` - данные вашего резюме
- `search_settings` - параметры поиска (город, опыт, лимит откликов)
- `llm_settings` - настройки Foundation Model
- `history_settings` - параметры работы с историей

### Использование конфига в коде

```python
from config_loader import load_config, get_resume_data, get_hh_credentials

config = load_config("config.json")
resume_data = get_resume_data(config)
login, password = get_hh_credentials(config)
```

## 📁 Структура проекта

```
job_searcher_agent/
├── graph_agent.py         # Основная логика мультиагентной системы
├── main.py                # Точка входа
├── config_loader.py       # Загрузка конфигурации
├── utils/
│   ├── storage.py         # Работа с историей сессий
│   └── __init__.py
├── data/
│   └── sessions/          # История откликов (JSON)
├── config.example.json    # Пример конфигурации
├── config.json            # Ваша конфигурация (не в git)
├── hide_me.py             # API ключ (не в git)
├── test_graph.py          # Тесты
├── GRAPH_AGENT_README.md  # Детальная документация
└── README.md              # Этот файл
```

## 🔍 Логирование

Система предоставляет детальное логирование всех действий:

```
🎯 SUPERVISOR: Анализ текущего состояния
📋 PLANNER: Создание/адаптация плана
🌐 BROWSER AGENT: Работа с браузером
✍️ COVER LETTER AGENT: Генерация письма
```

## 🐛 Troubleshooting

### Браузер не запускается

```bash
npx -y @playwright/mcp@latest
```

### Ошибка "config.json not found"

```bash
cp config.example.json config.json
# Отредактируйте config.json
```

### Ошибка "api_key not found"

Создайте `hide_me.py`:
```python
api_key = "your_api_key_here"
```

### Ошибка доступа к LLM

Проверьте:
- API key в `hide_me.py`
- Доступность API: `https://foundation-models.api.cloud.ru/v1`
- Лимиты на API

## 📈 Performance

- **Скорость**: ~1-2 минуты на один отклик
- **Рекомендуемый лимит**: 5-10 откликов за сессию
- **История**: последние 50 сессий для анализа

## 🛣️ Roadmap

- [x] Базовая мультиагентная система
- [x] Сохранение истории в JSON
- [x] Адаптивное планирование
- [x] Генерация писем через LLM
- [ ] Интеграция с Telegram для уведомлений
- [ ] ML-модель для предсказания успеха отклика
- [ ] Поддержка других job boards (Habr Career, LinkedIn)
- [ ] A/B тестирование стилей писем
- [ ] Web UI для управления

## 📚 Документация

- [GRAPH_AGENT_README.md](./GRAPH_AGENT_README.md) - Детальная документация архитектуры
- [PLAYWRIGHT_SETUP.md](./docs/PLAYWRIGHT_SETUP.md) - Настройка Playwright MCP
- [config.example.json](./config.example.json) - Пример конфигурации

## 🤝 Contributing

Contributions are welcome! Please read the contributing guidelines first.

## ⚠️ Отказ от ответственности

Этот проект предоставляется "как есть" без каких-либо гарантий. Автор не несет ответственности за любые последствия использования этого кода, включая, но не ограничиваясь:

- Нарушение условий использования сайтов (например, HeadHunter)
- Потерю или компрометацию учетных данных
- Неправильные или нежелательные отклики на вакансии
- Юридические проблемы или штрафы
- Потерю данных или повреждение системы

Пользователи запускают этот код на свой страх и риск. Рекомендуется тщательно тестировать систему в безопасной среде перед реальным использованием. Убедитесь, что вы соблюдаете все применимые законы и правила платформ.

## 📄 License

MIT License

## 🙏 Acknowledgments

- LangChain & LangGraph для мультиагентной системы
- Playwright MCP для автоматизации браузера
- Foundation Models (MiniMaxAI) для LLM

---

**Примечание**: Убедитесь, что файлы `config.json` и `hide_me.py` добавлены в `.gitignore` чтобы не публиковать credentials.

