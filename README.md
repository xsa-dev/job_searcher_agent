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

Нужны: [Hermes Agent](https://hermes-agent.nousresearch.com/docs/getting-started/installation), Node.js / `npx`, аккаунт HH, ключ cloud.ru (MiniMax, OpenAI-compatible), HTTP/SOCKS прокси для LLM.

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
# HTTP_PROXY=http://127.0.0.1:7890
NO_PROXY=hh.ru,.hh.ru,www.hh.ru,api.hh.ru,localhost,127.0.0.1
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

`HTTPS_PROXY` может быть `http://host:port` или `socks5://host:port`. Логин/пароль прокси клади в URL (`http://user:pass@host:port`), не в чат.

Модель уже прописана в `config.yaml`: `MiniMaxAI/MiniMax-M2` на `https://foundation-models.api.cloud.ru/v1` (`provider: custom`, не `minimax`).

Лимиты и «Для вас» — в `skills.config.jobsearcher` внутри `config.yaml`.

## LLM через proxy, HH без него

HH с VPN/прокси не открывается. Разделение такое:

- Запросы к LLM (cloud.ru) идут через `HTTPS_PROXY` в `.env`. Hermes отдаёт это в httpx (`HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY`).
- Браузер Playwright на hh.ru **не** должен идти в тот же прокси. В `.env` и в `mcp_servers.playwright.env` стоит `NO_PROXY` с `hh.ru`.

Если HH всё равно не грузится, проверь что системный VPN выключен для браузера, а прокси висит только на LLM.

## Запуск

```bash
job-searcher chat
# или:
hermes -p job-searcher
```

Первый заход: в чате «откликнись на вакансии как обычно». Браузер headed, чтобы пройти капчу / 2FA руками, если HH покажет.

Cron из дистрибутива **не включается сам**:

```bash
hermes -p job-searcher gateway start
hermes -p job-searcher cron list
# включи «HH daily auto-apply» когда логин уже стабильно проходит
```

После обновления профиля `config.yaml` у тебя сохранится. Чтобы подтянуть MCP/модель с апстрима:

```bash
hermes profile update job-searcher --force-config
```

## Скиллы

| Скилл | Роль |
|---|---|
| `hh-login` | Вход и проверка сессии |
| `hh-search` | «Для вас» или keyword search |
| `cover-letter` | Письмо 500–800 символов |
| `hh-apply` | Супервизор: цикл до лимита |

Инструменты браузера: `mcp_playwright_browser_click` / `browser_type` / `browser_snapshot`. Старые имена `Playwright_*` из прошлых доков не использовать.

## Отказ от ответственности

Автоотклики могут нарушать правила HH. Капча, бан, утечка пароля — твой риск. Сначала прогони 1 отклик и смотри глазами.

## Legacy: LangGraph

Старый запуск (`uv sync` + `uv run python main.py` + `config.json`) ещё в репозитории. Не основной путь. См. `mas/`, `docs/GRAPH_AGENT_README.md`.

## License

MIT. См. [LICENSE](./LICENSE).
