---
name: hh-search
description: >
  Find HeadHunter vacancies: default is the «Для вас» recommended feed
  (5–10 cards). Optional keyword search on hh.ru/search/vacancy. Skip URLs
  already applied. Use when the user asks to найти вакансии, Для вас, or
  before applying.
version: 1.0.0
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Jobs, HeadHunter, Browser]
    related_skills: [hh-login, hh-apply]
    config:
      - key: jobsearcher.use_recommended
        description: If true, use HH «Для вас» instead of keyword search
        default: "true"
        prompt: "Use recommended vacancies (Для вас)?"
      - key: jobsearcher.vacancy_search_query
        description: Keyword query when not using recommended feed
        default: "Python Backend разработчик"
      - key: jobsearcher.city
        description: City filter for keyword search
        default: "Москва"
---

# HH.ru search

Requires a logged-in session (`hh-login`). Tools: `mcp_playwright_browser_*`.

## Procedure

1. Confirm login (Резюме / Отклики vs Войти). If not logged in, run hh-login first.
2. If `skills.config.jobsearcher.use_recommended` is true:
   - Click «Для вас».
   - Scrape 5–10 vacancy cards: title, company, url, salary, location, experience, employment.
3. Else open `https://hh.ru/search/vacancy` and search with `vacancy_search_query` + city.
4. Drop URLs already stored as applied (MEMORY.md, previous STATUS DATA, `already_applied` in this session).
5. After 3 failed searches with zero new cards, STATUS: search_failed.

## DATA format

JSON list:

```json
[{
  "title": "...",
  "company": "...",
  "url": "https://hh.ru/vacancy/...",
  "salary": "200 000 – 300 000 ₽",
  "location": "Москва",
  "experience": "...",
  "employment": "full"
}]
```

```
STATUS: vacancies_found | search_failed
RESULT: N new vacancies
DATA: [ ... ]
```
