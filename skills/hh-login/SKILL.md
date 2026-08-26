---
name: hh-login
description: >
  Log in to HeadHunter (hh.ru) in a real browser via Playwright MCP and verify
  the session. Use when the user asks to войти на HH, check login, or before
  any search/apply loop.
version: 1.0.0
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Jobs, HeadHunter, Browser]
    related_skills: [hh-search, hh-apply]
required_environment_variables:
  - name: HH_LOGIN
    prompt: HeadHunter login (email)
    required_for: login
  - name: HH_PASSWORD
    prompt: HeadHunter password
    help: Never paste this into chat. Fill from the Playwright tool env / OS env.
    required_for: login
---

# HH.ru login

Drive the browser with Playwright MCP tools registered as `mcp_playwright_*`
(`browser_navigate`, `browser_snapshot`, `browser_click`, `browser_type` /
`browser_fill`). Do not use the old ExecuteAutomation names (`Playwright_navigate`).

## Procedure

1. Navigate to `https://hh.ru`.
2. Snapshot the page. Logged in if **at least 2** of these appear: резюме, профиль, отклики, сообщения, уведомления — **and** there is no explicit «Войти». **3+** of those menu items means logged in even if a «Войти» string still exists somewhere.
3. If not logged in, open the login form, fill email from `HH_LOGIN` and password from `HH_PASSWORD` via the fill/type tool (read values from the environment, never write them into your reasoning or STATUS).
4. Submit, wait, snapshot again, re-check step 2.
5. Captcha / 2FA: stop and tell the user to complete it in the headed browser, then re-check.

## Response

```
STATUS: logged_in | login_required | error
RESULT: ...
CONFIRMATION: ...
```

Never echo the password.
