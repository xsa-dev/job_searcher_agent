"""
Тесты для mas/supervisor_node.py
"""

import pytest
from mas.supervisor_node import supervisor_node
from mas.state import create_initial_state


def test_supervisor_no_plan_routes_to_planner(mock_resume_data):
    """Тест: нет плана → направляет к planner"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = ""  # Нет плана
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "planner"


def test_supervisor_max_applications_reached(mock_resume_data):
    """Тест: достигнут лимит → завершение"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=3
    )
    state["applied_count"] = 3  # Достигнут лимит
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "end"


def test_supervisor_browser_not_active(mock_resume_data):
    """Тест: браузер не активен → browser_agent"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = "Test plan"
    state["browser_session_active"] = False
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "browser_agent"


def test_supervisor_vacancy_without_letter(mock_resume_data, mock_vacancy):
    """Тест: есть вакансия без письма → cover_letter_agent"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = "Test plan"
    state["browser_session_active"] = True
    state["browser_status"] = "logged_in"
    state["vacancies"] = [mock_vacancy]
    state["current_vacancy"] = mock_vacancy
    state["cover_letter"] = ""
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "cover_letter_agent"


def test_supervisor_ready_to_apply(mock_resume_data, mock_vacancy):
    """Тест: есть письмо → browser_agent (отклик)"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = "Test plan"
    state["browser_session_active"] = True
    state["browser_status"] = "logged_in"
    state["vacancies"] = [mock_vacancy]
    state["current_vacancy"] = mock_vacancy
    state["cover_letter"] = "Отличное письмо"
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "browser_agent"


def test_supervisor_browser_error(mock_resume_data):
    """Тест: ошибка браузера → завершение"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["browser_status"] = "error"
    state["error_message"] = "Critical browser error"
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "end"


def test_supervisor_all_vacancies_processed(mock_resume_data, mock_vacancy):
    """Тест: все вакансии обработаны → завершение"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = "Test plan"
    state["browser_session_active"] = True
    state["vacancies"] = [mock_vacancy, mock_vacancy.copy()]
    state["current_vacancy_index"] = 2  # Все обработаны
    state["current_vacancy"] = None
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "end"


def test_supervisor_needs_vacancies(mock_resume_data):
    """Тест: браузер активен, нужно найти вакансии → browser_agent"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = "Test plan"
    state["browser_session_active"] = True
    state["browser_status"] = "logged_in"
    state["vacancies"] = []
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "browser_agent"


def test_supervisor_selects_next_vacancy(mock_resume_data, mock_vacancy):
    """Тест: выбор следующей вакансии из списка"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    state["plan"] = "Test plan"
    state["browser_session_active"] = True
    state["browser_status"] = "logged_in"
    state["vacancies"] = [mock_vacancy, mock_vacancy.copy()]
    state["current_vacancy_index"] = 0
    state["current_vacancy"] = None
    
    result = supervisor_node(state)
    
    assert result["next_agent"] == "cover_letter_agent"
    assert result["current_vacancy"] is not None
    assert result["current_vacancy"]["title"] == mock_vacancy["title"]

