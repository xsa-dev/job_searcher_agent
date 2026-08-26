---
name: cover-letter
description: >
  Write a 500–800 character Russian cover letter for one HH vacancy from
  resume env vars and the vacancy card. Use before submitting an application.
version: 1.0.0
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [Jobs, HeadHunter, Writing]
    related_skills: [hh-apply]
required_environment_variables:
  - name: RESUME_FULL_NAME
    prompt: Full name for the letter signature
    required_for: signature
---

# Cover letter

Do not invent a name, phone, email, GitHub, or LinkedIn. Read them from env:
`RESUME_FULL_NAME`, `RESUME_EMAIL`, `RESUME_PHONE`, `RESUME_TITLE`, `RESUME_TAGS`, `RESUME_SUMMARY`.
If a field is empty, omit it rather than filling a placeholder.

## Requirements

1. Length: 500–800 characters.
2. Language: Russian.
3. Structure: greeting + 2–3 skills matched to the vacancy + concrete offer + signature.
4. Personalize to vacancy title and company. Do not copy a generic template.
5. Signature: `RESUME_FULL_NAME`, then email and phone if set.

## Output

```
COVER_LETTER:
[text]
```

Then STATUS: letter_ready.
