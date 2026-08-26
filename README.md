# Job Searcher — Hermes-агент для HH.ru

Профиль [Nous Hermes Agent](https://hermes-agent.nousresearch.com/docs/). Два режима:

1. **Пакет** (по умолчанию, если не сказали «откликнись»): резюме → вакансии на hh.ru → письма, вилка, инструкция на Google Drive. **Сам никуда не жмёт «Откликнуться».**
2. **Автоотклик** (только по явной команде): логин → «Для вас»/поиск → письмо 500–800 → отклик → стоп по `max_applications`.

Если PDF-резюме ещё нет — сначала голосовое интервью по скиллу `resume-intake`, потом черновик резюме, потом пакет.

LangGraph в `mas/` и `main.py` — **legacy**. Рабочий путь — профиль Hermes.

## Как пользоваться

### 1. Есть PDF-резюме, нужен пакет без откликов

В чат:

```
Вот резюме. Найди ~100 вакансий на HH по Москве, собери письма и инструкцию, никуда не откликайся. Залей на Google Drive.
```

Агент: разберёт резюме, соберёт вакансии (офис/гибрид/удалёнка), разложит по фиту A/B/C, даст шаблоны писем, как просить зарплату, инструкцию «как откликаться». Кнопку отклика не трогает.

### 2. Резюме ещё нет (первый PDF)

```
Нужен сценарий под запись: я читаю вопросы, кандидат отвечает, помечаем факт/учёбу/хотелку. Создай папку на Диске.
```

Агент отдаёт скилл `resume-intake` и сценарий [`skills/resume-intake/references/interview-script.md`](skills/resume-intake/references/interview-script.md).

На встрече: один войс на всю беседу, телефон между вами. После каждого важного ответа вслух тег: **ФАКТ**, **УЧЁБА**, **ВМЕСТЕ**, **ХОТЕЛКА**, **НЕ БЫЛО**.

После встречи залей запись в папку на Диске и напиши агенту: «войс в папке, собери резюме». В текст резюме попадут только ФАКТ и УЧЁБА. Дальше — обычный пакет вакансий, снова без откликов.

### 3. Автоотклики (явно)

```
Откликнись на 5 вакансий из «Для вас».
```

Без этой фразы агент **не** жмёт отправить. Нужны `HH_LOGIN` / `HH_PASSWORD` в `.env` и российский `BROWSER_PROXY`.

Пароль HH **не** попадает в промпт модели.

## Установка

Нужны: [Hermes Agent](https://hermes-agent.nousresearch.com/docs/getting-started/installation), Node.js / `npx`, российский прокси для браузера. Модель — через `hermes setup model` (не cloud.ru).

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes setup model

hermes profile install github.com/xsa-dev/job_searcher_agent --alias
cp ~/.hermes/profiles/job-searcher/.env.EXAMPLE ~/.hermes/profiles/job-searcher/.env
hermes -p job-searcher setup model
```

Пока PR не в `main`, ставь с ветки:

```bash
hermes profile install github.com/xsa-dev/job_searcher_agent@hermes-profile --alias
```

Заполни `.env`:

```env
BROWSER_PROXY=socks5://user:pass@ru-proxy-host:port
HH_LOGIN=you@example.com
HH_PASSWORD=...
RESUME_FULL_NAME=...
RESUME_EMAIL=...
RESUME_PHONE=...
RESUME_TITLE=Python Backend Developer
RESUME_TAGS=Python, Django, FastAPI
RESUME_SUMMARY=...
DESIRED_SALARY=200000
```

Для только сбора резюме (`resume-intake`) логин HH можно не трогать, пока не перешли к поиску вакансий.

`BROWSER_PROXY` — только Playwright / hh.ru, российский IP. `http://` или `socks5://`.

LLM ходит через провайдера из `hermes setup model`. `OPENAI_API_KEY` и `HTTPS_PROXY` для cloud.ru не нужны.

## Запуск

```bash
job-searcher chat
```

Cron из дистрибутива не включается сам: `hermes -p job-searcher cron list`. Включай, только если хочешь ежедневные **авто**отклики.

## Скиллы

| Скилл | Роль |
|---|---|
| `resume-intake` | Первое резюме: сценарий на голос, теги факт/учёба/хотелка, черновик PDF |
| `hh-login` | Вход и проверка сессии |
| `hh-search` | «Для вас» или keyword search |
| `cover-letter` | Письмо 500–800 символов |
| `hh-apply` | Супервизор автооткликов: цикл до лимита |

## Отказ от ответственности

Автоотклики могут нарушать правила HH. Запускай на свой риск. Не выдумывай опыт в резюме.

## Legacy: LangGraph

`uv run python main.py` ещё в репозитории. Не основной путь.

## License

MIT. См. [LICENSE](./LICENSE).
