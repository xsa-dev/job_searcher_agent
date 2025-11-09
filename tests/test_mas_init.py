"""
Тесты для mas/__init__.py и обратной совместимости
"""

import pytest


def test_mas_imports():
    """Тест импортов из mas"""
    from mas import AgentState, create_initial_state, create_graph
    
    assert AgentState is not None
    assert callable(create_initial_state)
    assert callable(create_graph)


def test_mas_all_exports():
    """Тест что __all__ содержит нужные экспорты"""
    import mas
    
    assert hasattr(mas, '__all__')
    assert 'AgentState' in mas.__all__
    assert 'create_initial_state' in mas.__all__
    assert 'create_graph' in mas.__all__


def test_graph_agent_backward_compatibility():
    """Тест обратной совместимости через graph_agent.py"""
    from graph_agent import (
        AgentState,
        create_initial_state,
        create_graph,
        supervisor_node,
        planner_node,
        browser_agent_node,
        cover_letter_agent_node,
    )
    
    assert AgentState is not None
    assert callable(create_initial_state)
    assert callable(create_graph)
    assert callable(supervisor_node)
    assert callable(planner_node)
    assert callable(browser_agent_node)
    assert callable(cover_letter_agent_node)


def test_graph_agent_helper_functions():
    """Тест импорта вспомогательных функций через graph_agent.py"""
    from graph_agent import (
        _format_history_summary,
        _parse_plan,
        _parse_cover_letter,
        _get_successful_letters,
        _check_if_logged_in,
        _get_last_unfinished_plan,
    )
    
    assert callable(_format_history_summary)
    assert callable(_parse_plan)
    assert callable(_parse_cover_letter)
    assert callable(_get_successful_letters)
    assert callable(_check_if_logged_in)
    assert callable(_get_last_unfinished_plan)


def test_graph_agent_all_exports():
    """Тест что graph_agent экспортирует все нужные компоненты"""
    import graph_agent
    
    assert hasattr(graph_agent, '__all__')
    
    expected_exports = [
        'AgentState',
        'create_initial_state',
        'create_graph',
        'supervisor_node',
        'planner_node',
        'browser_agent_node',
        'cover_letter_agent_node',
        '_format_history_summary',
        '_parse_plan',
        '_parse_cover_letter',
        '_get_successful_letters',
        '_check_if_logged_in',
        '_get_last_unfinished_plan',
    ]
    
    for export in expected_exports:
        assert export in graph_agent.__all__, f"{export} missing in __all__"


def test_create_initial_state_works(mock_resume_data):
    """Тест что create_initial_state работает через оба импорта"""
    from mas import create_initial_state as mas_create
    from graph_agent import create_initial_state as ga_create
    
    state1 = mas_create(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    
    state2 = ga_create(
        user_request="Test",
        resume_data=mock_resume_data,
        hh_login="test",
        hh_password="test",
        max_applications=5
    )
    
    # Оба должны создавать валидные состояния
    assert state1["user_request"] == "Test"
    assert state2["user_request"] == "Test"
    assert state1["max_applications"] == 5
    assert state2["max_applications"] == 5

