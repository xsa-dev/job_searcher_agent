# HH.ru browser flow (ported from mas/browser_agent_node.py)

Use Microsoft Playwright MCP (`@playwright/mcp`), tool prefix `mcp_playwright_`.

| Action | Tool |
|---|---|
| Open URL | `browser_navigate` |
| See page | `browser_snapshot` |
| Click | `browser_click` |
| Type letter | `browser_type` (or `browser_fill`) |

Old docs mentioned `Playwright_navigate` / `playwright_get_visible_text` (ExecuteAutomation). Those names are wrong for the current MCP server.

## Login

1. `https://hh.ru`
2. Logged-in indicators (≥2, or ≥3 even if «Войти» exists): резюме, профиль, отклики, сообщения, уведомления, notifications, messages, responses.
3. Not-logged-in: войти, вход, sign in, log in.
4. Fill credentials from env via the type/fill tool. Never put the password in the skill prompt body.

## Search

- Default `use_recommended=true`: only the «Для вас» tab. Take 5–10 cards.
- Else: `https://hh.ru/search/vacancy` with query + city from skill config.

Card fields: title, company, url, salary, location, experience, employment.

## Apply

1. Open vacancy in a new tab.
2. No «Откликнуться» → already_applied.
3. Optional salary check on the page.
4. Fill name / phone / email from `RESUME_*` env if fields exist.
5. Paste letter (>50 characters).
6. Click send.
7. Confirm (sequence, or «отклик отправлен», or snapshot «ваш отклик отправлен»).
8. Close tab.

## Limits inherited from the old node

~50 ReAct iterations per run, wait between actions, headed browser (no `--headless` in shipped mcp args so first login/captcha is visible).
