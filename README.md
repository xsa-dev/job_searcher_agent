# Job Searcher — Hermes-агент для откликов на HH.ru

Профиль [Nous Hermes Agent](https://hermes-agent.nousresearch.com/docs/): логин на HeadHunter, лента «Для вас» (или поиск), короткое русское сопроводительное, отклик, стоп по лимиту, без повторных URL.

LangGraph-код в `mas/` и `main.py` — **legacy**. Рабочий путь — установка профиля Hermes.

## Что делает

1. Входит на [hh.ru](https://hh.ru) через Playwright MCP (живой браузер).
2. Берёт вакансии из «Для вас» (по умолчанию) или из поиска.
3. Пропускает уже откликнутые URL и вакансии ниже порога зарплаты (80% от `DESIRED_SALARY`).
4. Пишет письмо 500–800 символов на русском.
5. Жмёт «Откликнуться» / отправляет форму.
6. Останавливается на `max_applications` (по умолчанию 5).

Пароль HH **не** попадает в промпт модели. Только env.

## Установка

Нужны: [Hermes Agent](https://hermes-agent.nousresearch.com/docs/getting-started/installation), Node.js / `npx`, аккаунт HH, ключ cloud.ru, прокси для LLM и российский прокси для браузера.

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
hermes setup

hermes profile install github.com/xsa-dev/job_searcher_agent --alias
cp ~/.hermes/profiles/job-searcher/.env.EXAMPLE ~/.hermes/profiles/job-searcher/.env
```

Заполни `.env`:

```env
OPENAI_API_KEY=...
HTTPS_PROXY=http://127.0.0.1:7890
BROWSER_PROXY=http://user:pass@ru-proxy-host:port
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

Два разных прокси:
- `HTTPS_PROXY` — только LLM (cloud.ru).
- `BROWSER_PROXY` — только Playwright / hh.ru, российский IP. `http://` или `socks5://`.

Модель: `MiniMaxAI/MiniMax-M2` на `https://foundation-models.api.cloud.ru/v1` (`provider: custom`).

## Запуск

```bash
job-searcher chat
```

Cron из дистрибутива не включается сам: `hermes -p job-searcher cron list`.

## Скиллы

| Скилл | Роль |
|---|---|
| `hh-login` | Вход и проверка сессии |
| `hh-search` | «Для вас» или keyword search |
| `cover-letter` | Письмо 500–800 символов |
| `hh-apply` | Супервизор: цикл до лимита |

## Отказ от ответственности

Автоотклики могут нарушать правила HH. Запускай на свой риск.

## Legacy: LangGraph

`uv run python main.py` ещё в репозитории. Не основной путь.

## License

MIT. См. [LICENSE](./LICENSE).
