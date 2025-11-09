"""
Фикстуры для тестов мультиагентной системы
"""

import pytest
from unittest.mock import AsyncMock, Mock
from mas.state import create_initial_state


@pytest.fixture
def mock_resume_data():
    """Тестовые данные резюме"""
    return {
        "id": "test_resume",
        "title": "Python Backend Developer",
        "tags": ["Python", "Django", "FastAPI", "PostgreSQL"],
        "summary": "Опытный Python разработчик с 3+ годами опыта"
    }


@pytest.fixture
def mock_state(mock_resume_data):
    """Базовое состояние для тестов"""
    return create_initial_state(
        user_request="Тестовый запрос",
        resume_data=mock_resume_data,
        hh_login="test@test.com",
        hh_password="test_password",
        max_applications=5,
    )


@pytest.fixture
def mock_sessions():
    """Тестовые данные предыдущих сессий"""
    return [
        {
            "timestamp": "2025-11-07T10:00:00",
            "plan": "Тестовый план",
            "plan_steps": ["Шаг 1", "Шаг 2"],
            "statistics": {
                "total_vacancies_found": 10,
                "total_applied": 5,
                "average_score": 0.85
            },
            "vacancies_processed": [
                {
                    "title": "Python Developer",
                    "company": "Test Company",
                    "applied": True,
                    "score": 0.85,
                    "cover_letter": "Отличное письмо для отличной вакансии..."
                }
            ]
        },
        {
            "timestamp": "2025-11-06T10:00:00",
            "plan": "",
            "plan_steps": [],
            "statistics": {
                "total_vacancies_found": 8,
                "total_applied": 3,
                "average_score": 0.75
            }
        }
    ]


@pytest.fixture
def mock_vacancy():
    """Тестовая вакансия"""
    return {
        "title": "Python Backend Developer",
        "company": "Test Company",
        "url": "https://test.com/vacancy/123",
        "description": "Ищем опытного Python разработчика",
        "requirements": "Python, Django, REST API",
        "score": 0.85,
        "applied": False
    }


@pytest.fixture
def mock_llm():
    """Мок ChatOpenAI модели"""
    mock = AsyncMock()
    mock_response = Mock()
    mock_response.content = "Test response"
    mock.ainvoke = AsyncMock(return_value=mock_response)
    return mock


@pytest.fixture
def mock_tools():
    """Мок MCP инструментов"""
    tools = []
    
    # Playwright_navigate
    nav_tool = Mock()
    nav_tool.name = "Playwright_navigate"
    nav_tool.ainvoke = AsyncMock(return_value="Navigated successfully")
    tools.append(nav_tool)
    
    # playwright_get_visible_text
    snap_tool = Mock()
    snap_tool.name = "playwright_get_visible_text"
    snap_tool.ainvoke = AsyncMock(return_value="Page content snapshot")
    tools.append(snap_tool)
    
    # Playwright_click
    click_tool = Mock()
    click_tool.name = "Playwright_click"
    click_tool.ainvoke = AsyncMock(return_value="Clicked successfully")
    tools.append(click_tool)
    
    # Playwright_fill
    type_tool = Mock()
    type_tool.name = "Playwright_fill"
    type_tool.ainvoke = AsyncMock(return_value="Filled successfully")
    tools.append(type_tool)
    
    return tools

