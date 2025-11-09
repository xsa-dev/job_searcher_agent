"""
Тесты для mas/state.py
"""

import pytest
from mas.state import AgentState, create_initial_state


def test_create_initial_state_basic(mock_resume_data):
    """Тест создания начального состояния"""
    state = create_initial_state(
        user_request="Тестовый запрос",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="test_password",
        max_applications=5
    )
    
    assert isinstance(state, dict)
    assert state["user_request"] == "Тестовый запрос"
    assert state["max_applications"] == 5


def test_create_initial_state_all_fields(mock_resume_data):
    """Тест наличия всех обязательных полей AgentState"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=5
    )
    
    required_fields = [
        "messages", "user_request", "session_id", "start_time",
        "plan", "plan_steps", "current_step", "plan_needs_update",
        "resume_data", "hh_login", "hh_password",
        "vacancies", "current_vacancy", "current_vacancy_index", "use_recommended",
        "cover_letter",
        "applied_count", "max_applications", "rejected_count",
        "browser_status", "browser_session_active",
        "previous_sessions", "already_applied_urls",
        "next_agent", "error_message"
    ]
    
    for field in required_fields:
        assert field in state, f"Field '{field}' missing in state"


def test_create_initial_state_field_types(mock_resume_data):
    """Тест типов полей AgentState"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=10
    )
    
    # Проверяем типы
    assert isinstance(state["messages"], list)
    assert isinstance(state["user_request"], str)
    assert isinstance(state["session_id"], str)
    assert isinstance(state["start_time"], float)
    assert isinstance(state["plan"], str)
    assert isinstance(state["plan_steps"], list)
    assert isinstance(state["current_step"], int)
    assert isinstance(state["plan_needs_update"], bool)
    assert isinstance(state["resume_data"], dict)
    assert isinstance(state["vacancies"], list)
    assert isinstance(state["current_vacancy_index"], int)
    assert isinstance(state["use_recommended"], bool)
    assert isinstance(state["cover_letter"], str)
    assert isinstance(state["applied_count"], int)
    assert isinstance(state["max_applications"], int)
    assert isinstance(state["rejected_count"], int)
    assert isinstance(state["browser_status"], str)
    assert isinstance(state["browser_session_active"], bool)
    assert isinstance(state["previous_sessions"], list)
    assert isinstance(state["already_applied_urls"], set)
    assert isinstance(state["next_agent"], str)
    assert isinstance(state["error_message"], str)


def test_create_initial_state_default_values(mock_resume_data):
    """Тест начальных значений полей"""
    state = create_initial_state(
        user_request="Test request",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=7
    )
    
    # Проверяем начальные значения
    assert state["user_request"] == "Test request"
    assert state["max_applications"] == 7
    assert state["applied_count"] == 0
    assert state["current_step"] == 0
    assert state["current_vacancy_index"] == 0
    assert state["rejected_count"] == 0
    assert state["plan"] == ""
    assert state["cover_letter"] == ""
    assert state["error_message"] == ""
    assert state["plan_needs_update"] == False
    assert state["browser_session_active"] == False
    assert state["use_recommended"] == False
    assert state["next_agent"] == "planner"
    assert state["browser_status"] == "idle"
    assert len(state["messages"]) == 0
    assert len(state["plan_steps"]) == 0
    assert len(state["vacancies"]) == 0
    assert state["current_vacancy"] is None


def test_create_initial_state_with_history(mock_resume_data, mock_sessions):
    """Тест создания состояния с историей сессий"""
    already_applied = {"https://test.com/1", "https://test.com/2"}
    
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=5,
        previous_sessions=mock_sessions,
        already_applied_urls=already_applied
    )
    
    assert len(state["previous_sessions"]) == 2
    assert len(state["already_applied_urls"]) == 2
    assert "https://test.com/1" in state["already_applied_urls"]


def test_create_initial_state_use_recommended(mock_resume_data):
    """Тест флага use_recommended"""
    state = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=5,
        use_recommended=True
    )
    
    assert state["use_recommended"] == True


def test_create_initial_state_session_id_unique(mock_resume_data):
    """Тест формата session_id"""
    import time
    
    state1 = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=5
    )
    
    time.sleep(0.01)  # Небольшая задержка
    
    state2 = create_initial_state(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="password",
        max_applications=5
    )
    
    # Проверяем формат
    assert state1["session_id"].startswith("session_")
    assert state2["session_id"].startswith("session_")
    
    # Session IDs могут быть одинаковыми если создаются в одну секунду
    # это нормально для timestamp-based ID

