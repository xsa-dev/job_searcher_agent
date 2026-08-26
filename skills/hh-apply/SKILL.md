---
name: hh-apply
description: >
  Full HH.ru auto-apply loop: login, find vacancies (Для вас or search), skip
  duplicates and low salary, write a Russian cover letter, submit the application,
  stop at max_applications. Use for откликнуться, auto-apply, daily job loop.
version: 1.0.0
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Jobs, HeadHunter, Browser]
    related_skills: [hh-login, hh-search, cover-letter]
    config:
      - key: jobsearcher.max_applications
        description: Max applications per run
        default: "5"
        prompt: "How many applications per run?"
      - key: jobsearcher.use_recommended
        description: If true, use HH «Для вас» instead of search
        default: "true"
      - key: jobsearcher.salary_threshold
        description: Skip vacancy if its salary max < desired * this fraction
        default: "0.8"
required_environment_variables:
  - name: HH_LOGIN
    prompt: HeadHunter login (email)
    required_for: login
  - name: HH_PASSWORD
    prompt: HeadHunter password
    help: Never paste this into chat
    required_for: login
---

# HH.ru auto-apply

Read [status-machine.md](references/status-machine.md) and [hh-flow.md](references/hh-flow.md) before acting.

This skill is the supervisor. Do not skip steps. LangGraph `mas/` in this repo is legacy.

Playwright MCP tools: `mcp_playwright_browser_navigate`, `mcp_playwright_browser_snapshot`, `mcp_playwright_browser_click`, `mcp_playwright_browser_type` (or `browser_fill`). Never the old `Playwright_*` names.

## Loop (same as the old graph)

1. If not logged in → hh-login.
2. If no vacancy list → hh-search.
3. Pick next vacancy not in `already_applied` URLs.
4. Salary skip: if `DESIRED_SALARY` is set and vacancy salary max < desired * `jobsearcher.salary_threshold` (default 0.8), skip.
5. Open vacancy (new tab). If there is no «Откликнуться» (page shows «Отклик отправлен») → already_applied, close tab, next.
6. cover-letter for this vacancy.
7. Fill name/phone/email from env if the form asks. Paste the letter. Click send.
8. Confirm apply (see below). Close tab. Increment applied_count. Remember the URL.
9. Repeat until `applied_count >= max_applications` or 3 failed searches.

## Apply confirmation (OR)

A successful apply is confirmed only if at least one of:

- Tool sequence: click «Откликнуться» → type letter (>50 chars) → click «Отправить» / submit.
- Page text: «ОТКЛИК ОТПРАВЛЕН» / «Отклик отправлен» / «application sent».
- Snapshot contains «ваш отклик отправлен».

Then write **ОТКЛИК ОТПРАВЛЕН** in CONFIRMATION and name the vacancy + company.

## Never

- Interpolate `HH_PASSWORD` into the prompt, STATUS, or logs.
- Hardcode a person's name, phone, or email. Env only.
- Continue after `browser_status == error` with retries exhausted.
- Re-apply a URL from this session or MEMORY.md applied list.

## Response per vacancy

```
STATUS: application_sent | already_applied | salary_too_low | error
RESULT: ...
CONFIRMATION: ОТКЛИК ОТПРАВЛЕН | skipped
DATA: {"url": "...", "title": "...", "company": "..."}
```

After the cap: STATUS: end. Scheduled runs with nothing new: `[SILENT]`.
