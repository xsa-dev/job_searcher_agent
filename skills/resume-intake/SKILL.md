---
name: resume-intake
description: >
  Collect a first HH.ru resume from a spoken interview or a voice recording.
  Use when there is no resume PDF yet, the candidate is a first-time job seeker,
  or the user wants a script tagged ФАКТ / УЧЁБА / ХОТЕЛКА. After intake, draft
  the resume from FACT/STUDY only, then the vacancy pack. Do not auto-apply
  unless the user explicitly asks to откликнуться.
version: 1.0.0
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Jobs, HeadHunter, Resume, Interview]
    related_skills: [hh-search, cover-letter]
---

# First resume from a voice interview

Read [interview-script.md](references/interview-script.md) and give that script to the interviewer (or read it yourself). One audio file for the whole meeting.

This skill is **not** hh-apply. Default after intake: draft resume + vacancy pack. Click «Откликнуться» only if the user said so in this turn.

## When to use

- No PDF resume yet.
- New candidate, student, first job.
- User will record a conversation and drop the voice file.

If a resume PDF already exists, skip this skill. Parse the PDF and go to search/pack.

## Tags (spoken after important answers)

| Tag | Meaning | Resume |
|---|---|---|
| ФАКТ | Candidate actually did it | yes |
| УЧЁБА | Course, diploma, study project | education / projects |
| ВМЕСТЕ | Team work, own role unclear | only with a concrete own verb |
| ХОТЕЛКА | Wants it, has not done it | desired title / about only |
| НЕ БЫЛО | Did not happen | never |

If unsure, do not tag ФАКТ.

## Pipeline

1. Hand the interviewer the script (or run the questions live).
2. One voice file for the whole meeting. Phone between the two people.
3. After the file lands: transcribe. Keep answers with ФАКТ and УЧЁБА. Drop НЕ БЫЛО. Map ХОТЕЛКА to the desired role, not to experience.
4. Draft a first HH-style resume (markdown, then PDF if tools allow). One headline, not three roles with slashes. No invented numbers, employers, or skills.
5. Then the pack: search HH,  ~100 matches, cover-letter templates, salary how-to, Drive folder. **Do not apply.**
6. Fill `RESUME_*` env from the draft only after the user confirms the resume text.

## Never

- Invent experience to fill empty years.
- Write «коммуникабельна, стрессоустойчива» instead of a concrete sentence.
- Auto-apply from this skill.
- Put HH_PASSWORD, proxy, or secrets in the script or the resume.

## Response

```
STATUS: script_ready | intake_recorded | resume_draft | pack_ready
RESULT: ...
DATA: {"tags_used": [], "headline": "...", "drive_folder": "..."}
```
