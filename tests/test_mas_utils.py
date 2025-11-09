"""
Тесты для mas/utils.py
"""

import pytest
from mas.utils import (
    _format_history_summary,
    _parse_plan,
    _parse_cover_letter,
    _get_successful_letters,
    _get_last_unfinished_plan,
)


def test_format_history_summary_with_data(mock_sessions):
    """Тест форматирования истории с данными"""
    summary = _format_history_summary(mock_sessions)
    
    assert "Сессия" in summary
    assert "0.85" in summary
    assert "2025-11-07" in summary
    assert "Найдено" in summary
    assert "Откликов" in summary


def test_format_history_summary_empty():
    """Тест форматирования пустой истории"""
    summary = _format_history_summary([])
    
    assert summary == "История отсутствует"


def test_parse_plan_correct_format():
    """Тест парсинга плана с корректным форматом"""
    plan_text = """
PLAN:
Это детальный план работы.
Включает несколько строк.

STEPS:
1. Логин на HeadHunter
2. Поиск вакансий
3. Отправка откликов
"""
    
    plan, steps = _parse_plan(plan_text)
    
    assert "детальный план" in plan
    assert len(steps) == 3
    assert "Логин на HeadHunter" in steps[0]
    assert "Поиск вакансий" in steps[1]
    assert "Отправка откликов" in steps[2]


def test_parse_plan_with_dashes():
    """Тест парсинга плана с тире вместо номеров"""
    plan_text = """
PLAN:
План работы

STEPS:
- Первый шаг
- Второй шаг
"""
    
    plan, steps = _parse_plan(plan_text)
    
    assert len(steps) == 2
    assert "Первый шаг" in steps[0]


def test_parse_plan_no_markers():
    """Тест парсинга плана без маркеров"""
    plan_text = "Просто план без маркеров\nНа несколько строк"
    
    plan, steps = _parse_plan(plan_text)
    
    assert isinstance(plan, str)
    assert isinstance(steps, list)


def test_parse_cover_letter_with_marker():
    """Тест парсинга письма с маркером"""
    letter_text = """
COVER_LETTER:
Здравствуйте!

Я хотел бы откликнуться на вашу вакансию...
"""
    
    letter = _parse_cover_letter(letter_text)
    
    assert "Здравствуйте" in letter
    assert "COVER_LETTER:" not in letter


def test_parse_cover_letter_without_marker():
    """Тест парсинга письма без маркера"""
    letter_text = "Просто текст письма"
    
    letter = _parse_cover_letter(letter_text)
    
    assert letter == "Просто текст письма"


def test_get_successful_letters_with_data(mock_sessions):
    """Тест извлечения успешных писем"""
    examples = _get_successful_letters(mock_sessions)
    
    assert "Python Developer" in examples
    assert "0.85" in examples
    assert "Отличное письмо" in examples


def test_get_successful_letters_filters_low_score():
    """Тест фильтрации писем с низким score"""
    sessions = [
        {
            "vacancies_processed": [
                {
                    "title": "Good Vacancy",
                    "applied": True,
                    "score": 0.85,
                    "cover_letter": "Good letter"
                },
                {
                    "title": "Bad Vacancy",
                    "applied": True,
                    "score": 0.6,  # Низкий score
                    "cover_letter": "Bad letter"
                }
            ]
        }
    ]
    
    examples = _get_successful_letters(sessions)
    
    assert "Good Vacancy" in examples
    assert "Bad Vacancy" not in examples


def test_get_successful_letters_empty():
    """Тест извлечения писем из пустых сессий"""
    examples = _get_successful_letters([])
    
    assert examples == "Примеров пока нет"


def test_get_last_unfinished_plan_with_plan():
    """Тест извлечения плана из истории"""
    # Создаем сессию с планом как последнюю
    sessions_with_plan = [
        {
            "timestamp": "2025-11-06T10:00:00",
            "plan": "",
            "plan_steps": [],
            "statistics": {
                "total_vacancies_found": 8,
                "total_applied": 3,
                "average_score": 0.75
            }
        },
        {
            "timestamp": "2025-11-07T10:00:00",
            "plan": "Тестовый план работы с вакансиями на HeadHunter. Включает поиск, анализ и отклики на релевантные позиции.",
            "plan_steps": ["Шаг 1", "Шаг 2"],
            "statistics": {
                "total_vacancies_found": 10,
                "total_applied": 5,
                "average_score": 0.85
            }
        }
    ]
    
    result = _get_last_unfinished_plan(sessions_with_plan)
    
    assert result is not None
    assert "plan" in result
    assert "plan_steps" in result
    assert "Тестовый план" in result["plan"]
    assert len(result["plan_steps"]) == 2


def test_get_last_unfinished_plan_without_plan():
    """Тест извлечения плана когда его нет"""
    sessions = [
        {
            "timestamp": "2025-11-07T10:00:00",
            "plan": "",
            "plan_steps": []
        }
    ]
    
    result = _get_last_unfinished_plan(sessions)
    
    assert result is None


def test_get_last_unfinished_plan_empty_sessions():
    """Тест извлечения плана из пустой истории"""
    result = _get_last_unfinished_plan([])
    
    assert result is None


@pytest.mark.asyncio
async def test_check_if_logged_in_success(mock_tools):
    """Тест проверки авторизации - успешно"""
    from mas.utils import _check_if_logged_in
    
    # Создаем snapshot tool с индикаторами авторизации
    tools_dict = {}
    snap_tool = mock_tools[1]  # playwright_get_visible_text
    snap_tool.ainvoke.return_value = "Резюме Отклики Сообщения Page content"
    tools_dict["playwright_get_visible_text"] = snap_tool
    
    result = await _check_if_logged_in(tools_dict)
    
    assert result == True


@pytest.mark.asyncio
async def test_check_if_logged_in_not_logged():
    """Тест проверки авторизации - не авторизован"""
    from unittest.mock import AsyncMock, Mock
    from mas.utils import _check_if_logged_in
    
    snap_tool = Mock()
    snap_tool.ainvoke = AsyncMock(return_value="Войти Page content")
    tools_dict = {"playwright_get_visible_text": snap_tool}
    
    result = await _check_if_logged_in(tools_dict)
    
    assert result == False

