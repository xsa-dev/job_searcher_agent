# Status machine (ported from mas/supervisor_node.py)

Statuses: `idle` | `logged_in` | `vacancies_found` | `application_sent` | `already_applied` | `salary_too_low` | `search_failed` | `error` | `end`

Routing (deterministic, not an LLM):

- no plan → treat as login → search → apply loop (do not ask the planner model unless the user requested a custom plan)
- not logged in or browser idle → hh-login
- logged in + no vacancies → hh-search
- vacancy without letter → cover-letter
- vacancy + letter → apply in browser
- after `application_sent` → next vacancy, or search more if under cap
- `applied_count >= max_applications` → end
- `search_attempts >= 3` → error/end
- `browser_status == error` and retries exhausted → end

Salary skip before opening a vacancy: `desired * 0.8` (see `mas/utils.py`). Missing salary on either side → do not filter.

Persist applied URLs in MEMORY.md / session notes so the next run skips them (old code kept last 30 URLs in JSON sessions).
