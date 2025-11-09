# Chroma MCP Server Integration

Интеграция векторного хранилища Chroma в мультиагентную систему для семантического поиска и хранения данных о вакансиях, сопроводительных письмах и истории откликов.

## Возможности

### 1. Векторное хранилище вакансий
- **Семантический поиск** похожих вакансий
- **Автоматическая дедупликация** при обнаружении повторяющихся вакансий
- **Индексация метаданных**: URL, компания, зарплата, score соответствия
- **История откликов** с возможностью поиска успешных паттернов

### 2. Хранилище сопроводительных писем
- **Поиск похожих писем** для новых вакансий
- **Фильтрация по успешности** (только успешные отклики)
- **Контекстуальные примеры** для генерации новых писем
- **Метаданные**: вакансия, компания, длина письма, успешность

### 3. Индексация резюме
- **Векторизация навыков** и опыта
- **Семантический поиск** релевантных вакансий
- **Улучшенное соответствие** вакансиям

## Архитектура

### Коллекции в Chroma

```
chroma_data/
├── job_vacancies/       # Все вакансии с эмбеддингами
├── cover_letters/       # Сопроводительные письма
└── resume_data/         # Навыки и данные резюме
```

### Интеграция в агенты

#### Browser Agent
- Инициализация коллекций при первом запуске
- Сохранение вакансий после отправки отклика
- Автоматическая индексация метаданных
- Обработка дубликатов

#### Cover Letter Agent
- Поиск похожих успешных писем (top-3)
- Использование примеров из Chroma в промпте
- Сохранение созданного письма с метаданными

#### Planner Agent
- Индексация навыков резюме
- Поиск истории успешных вакансий (top-5)
- Анализ паттернов для создания плана

## Использование

### 1. Запуск Chroma MCP Server

```bash
# Запустить сервер
make chroma-start

# Проверить статус
make chroma-status

# Остановить сервер
make chroma-stop

# Перезапустить
make chroma-restart

# Очистить все данные
make chroma-clean
```

### 2. Конфигурация

В `config.json` добавьте:

```json
{
  "chroma_settings": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8091,
    "persist_directory": "./chroma_data",
    "collections": {
      "vacancies": "job_vacancies",
      "cover_letters": "cover_letters",
      "resume": "resume_data"
    }
  }
}
```

### 3. Использование в коде

```python
from mas import create_initial_state

# Создание состояния с включенным Chroma
state = create_initial_state(
    user_request="Откликнуться на 5 вакансий Python разработчика",
    resume_data=resume_data,
    hh_login="login@example.com",
    hh_password="password",
    max_applications=5,
    chroma_enabled=True  # Включить Chroma
)
```

### 4. API утилит Chroma

#### Работа с вакансиями

```python
from mas.chroma_utils import (
    store_vacancy,
    search_similar_vacancies,
    check_vacancy_duplicate,
    get_vacancy_history,
)

# Сохранить вакансию
await store_vacancy(chroma_tools, vacancy_data, session_id)

# Поиск похожих вакансий
results = await search_similar_vacancies(
    chroma_tools,
    "Python Backend разработчик с Django",
    n_results=5
)

# Проверка дубликата
is_duplicate = await check_vacancy_duplicate(
    chroma_tools,
    "https://hh.ru/vacancy/12345"
)

# История вакансий
history = await get_vacancy_history(
    chroma_tools,
    "Python Developer",
    n_results=10
)
```

#### Работа с письмами

```python
from mas.chroma_utils import (
    store_cover_letter,
    get_similar_cover_letters,
)

# Сохранить письмо
await store_cover_letter(
    chroma_tools,
    vacancy,
    cover_letter_text,
    session_id,
    was_successful=True
)

# Поиск похожих писем
similar = await get_similar_cover_letters(
    chroma_tools,
    vacancy,
    n_results=3,
    only_successful=True
)
```

#### Работа с резюме

```python
from mas.chroma_utils import store_resume_skills

# Индексировать навыки резюме
await store_resume_skills(chroma_tools, resume_data)
```

## Преимущества интеграции

### ✅ Улучшенное качество откликов
- Примеры успешных писем из истории
- Анализ паттернов работающих стратегий
- Персонализация на основе семантического поиска

### ✅ Избежание дубликатов
- Автоматическая проверка повторных вакансий
- Векторный поиск похожих вакансий
- История всех обработанных вакансий

### ✅ Умное планирование
- Анализ успешных сессий
- Поиск похожих ситуаций в истории
- Адаптивные стратегии на основе данных

### ✅ Семантический поиск
- Поиск по смыслу, а не точному совпадению
- Нахождение релевантных примеров
- Кросс-референсы между вакансиями и письмами

## Структура файлов

```
mas/
├── chroma_utils.py           # Утилиты для работы с Chroma
├── browser_agent_node.py     # Интеграция в Browser Agent
├── cover_letter_agent_node.py # Интеграция в Cover Letter Agent
├── planner_node.py           # Интеграция в Planner
├── state.py                  # Новые поля: chroma_enabled, chroma_collections_ready
├── prompts.py                # Обновленные промпты с упоминанием Chroma
└── CHROMA_INTEGRATION.md     # Эта документация
```

## Отключение Chroma

Если нужно отключить Chroma:

```python
# В config.json
{
  "chroma_settings": {
    "enabled": false
  }
}

# Или при создании состояния
state = create_initial_state(
    ...,
    chroma_enabled=False
)
```

## Troubleshooting

### Проблема: Chroma MCP Server не запускается

```bash
# Проверьте логи
tail -f logs/chroma_mcp_server.log

# Убедитесь что порт 8091 свободен
lsof -i :8091

# Попробуйте перезапустить
make chroma-restart
```

### Проблема: Коллекции не создаются

Проверьте права доступа к директории:

```bash
ls -la chroma_data/
chmod -R 755 chroma_data/
```

### Проблема: Низкая точность поиска

Увеличьте количество результатов:

```python
results = await search_similar_vacancies(
    chroma_tools,
    query,
    n_results=10  # Было 5
)
```

## Дополнительная информация

- Chroma использует эмбеддинги для векторного поиска
- Данные хранятся локально в `./chroma_data/`
- Бэкап данных: просто скопируйте `chroma_data/`
- Миграция: перенесите директорию `chroma_data/` на новую машину

## Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/chroma_mcp_*.log`
2. Убедитесь что Chroma MCP Server запущен (`make chroma-status`)
3. Проверьте конфигурацию в `config.json`
4. Попробуйте очистить данные (`make chroma-clean`) и начать заново


