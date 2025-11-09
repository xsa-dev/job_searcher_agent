"""
Тесты для mas/prompts.py
"""

import pytest
from mas.prompts import (
    SUPERVISOR_PROMPT,
    PLANNER_PROMPT,
    BROWSER_AGENT_PROMPT,
    COVER_LETTER_AGENT_PROMPT,
)


def test_supervisor_prompt_format():
    """Тест форматирования SUPERVISOR_PROMPT"""
    formatted = SUPERVISOR_PROMPT.format(
        plan="Test plan",
        current_step=1,
        total_steps=5,
        applied_count=2,
        max_applications=5,
        browser_status="logged_in",
        vacancies_count=10,
        current_vacancy_title="Python Developer"
    )
    
    assert "Test plan" in formatted
    assert "1/5" in formatted
    assert "2/5" in formatted
    assert "logged_in" in formatted
    assert "10" in formatted
    assert "Python Developer" in formatted


def test_supervisor_prompt_contains_keywords():
    """Тест наличия ключевых слов в SUPERVISOR_PROMPT"""
    assert "Supervisor" in SUPERVISOR_PROMPT
    assert "planner" in SUPERVISOR_PROMPT
    assert "browser_agent" in SUPERVISOR_PROMPT
    assert "cover_letter_agent" in SUPERVISOR_PROMPT
    assert "end" in SUPERVISOR_PROMPT


def test_planner_prompt_format():
    """Тест форматирования PLANNER_PROMPT"""
    formatted = PLANNER_PROMPT.format(
        user_request="Найти вакансии",
        resume_title="Python Developer",
        resume_tags="Python, Django",
        resume_summary="Опытный разработчик",
        sessions_count=3,
        history_summary="История сессий",
        applied_count=5,
        max_applications=10,
        vacancies_count=20,
        already_applied_count=15
    )
    
    assert "Найти вакансии" in formatted
    assert "Python Developer" in formatted
    assert "Python, Django" in formatted
    assert "3 сессий" in formatted
    assert "5/10" in formatted


def test_planner_prompt_contains_keywords():
    """Тест наличия ключевых слов в PLANNER_PROMPT"""
    assert "Planner" in PLANNER_PROMPT
    assert "PLAN:" in PLANNER_PROMPT
    assert "STEPS:" in PLANNER_PROMPT
    assert "HeadHunter" in PLANNER_PROMPT


def test_browser_agent_prompt_format():
    """Тест форматирования BROWSER_AGENT_PROMPT"""
    formatted = BROWSER_AGENT_PROMPT.format(
        current_plan_step="Логин на сайт",
        hh_login="test@test.com",
        hh_password="password123",
        browser_active=True,
        browser_status="idle",
        browser_instructions="Инструкции для агента"
    )
    
    assert "Логин на сайт" in formatted
    assert "test@test.com" in formatted
    assert "password123" in formatted
    assert "True" in formatted
    assert "idle" in formatted
    assert "Инструкции для агента" in formatted


def test_browser_agent_prompt_contains_keywords():
    """Тест наличия ключевых слов в BROWSER_AGENT_PROMPT"""
    assert "Browser Agent" in BROWSER_AGENT_PROMPT
    assert "Playwright_navigate" in BROWSER_AGENT_PROMPT
    assert "playwright_get_visible_text" in BROWSER_AGENT_PROMPT
    assert "Playwright_click" in BROWSER_AGENT_PROMPT
    assert "Playwright_fill" in BROWSER_AGENT_PROMPT
    assert "playwright_click_and_switch_tab" in BROWSER_AGENT_PROMPT
    assert "wait" in BROWSER_AGENT_PROMPT
    assert "STATUS:" in BROWSER_AGENT_PROMPT


def test_cover_letter_agent_prompt_format():
    """Тест форматирования COVER_LETTER_AGENT_PROMPT"""
    formatted = COVER_LETTER_AGENT_PROMPT.format(
        resume_title="Python Developer",
        resume_tags="Python, Django",
        resume_summary="Опытный разработчик",
        vacancy_title="Senior Python Developer",
        vacancy_company="Test Company",
        vacancy_description="Описание вакансии",
        vacancy_requirements="Python, Django, REST",
        vacancy_score=0.85,
        successful_letters_examples="Примеры писем"
    )
    
    assert "Python Developer" in formatted
    assert "Python, Django" in formatted
    assert "Senior Python Developer" in formatted
    assert "Test Company" in formatted
    assert "0.85" in formatted
    assert "Примеры писем" in formatted


def test_cover_letter_agent_prompt_contains_keywords():
    """Тест наличия ключевых слов в COVER_LETTER_AGENT_PROMPT"""
    assert "Cover Letter Agent" in COVER_LETTER_AGENT_PROMPT
    assert "COVER_LETTER:" in COVER_LETTER_AGENT_PROMPT
    assert "500-1000" in COVER_LETTER_AGENT_PROMPT
    assert "русском языке" in COVER_LETTER_AGENT_PROMPT


def test_all_prompts_are_strings():
    """Тест что все промпты - строки"""
    assert isinstance(SUPERVISOR_PROMPT, str)
    assert isinstance(PLANNER_PROMPT, str)
    assert isinstance(BROWSER_AGENT_PROMPT, str)
    assert isinstance(COVER_LETTER_AGENT_PROMPT, str)


def test_all_prompts_not_empty():
    """Тест что промпты не пустые"""
    assert len(SUPERVISOR_PROMPT) > 0
    assert len(PLANNER_PROMPT) > 0
    assert len(BROWSER_AGENT_PROMPT) > 0
    assert len(COVER_LETTER_AGENT_PROMPT) > 0

