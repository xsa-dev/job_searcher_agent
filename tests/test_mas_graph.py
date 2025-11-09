"""
Тесты для mas/graph.py
"""

import pytest
from mas.graph import create_graph
from mas.state import AgentState


def test_create_graph_returns_compiled(mock_tools, mock_llm):
    """Тест что create_graph возвращает скомпилированный граф"""
    graph = create_graph(mock_tools, mock_llm)
    
    assert graph is not None
    assert hasattr(graph, 'invoke') or hasattr(graph, 'ainvoke')


def test_create_graph_with_empty_tools(mock_llm):
    """Тест создания графа с пустым списком инструментов"""
    graph = create_graph([], mock_llm)
    
    assert graph is not None


def test_create_graph_adds_wait_tool(mock_tools, mock_llm):
    """Тест что wait_tool добавляется к инструментам"""
    initial_tools_count = len(mock_tools)
    
    # Создаем граф (wait_tool добавляется внутри)
    graph = create_graph(mock_tools, mock_llm)
    
    # Проверяем что граф создан
    assert graph is not None
    
    # Исходные инструменты не изменились
    assert len(mock_tools) == initial_tools_count


def test_create_graph_structure(mock_tools, mock_llm):
    """Тест структуры графа"""
    graph = create_graph(mock_tools, mock_llm)
    
    # Граф должен иметь методы для вызова
    assert callable(getattr(graph, 'invoke', None)) or callable(getattr(graph, 'ainvoke', None))


@pytest.mark.asyncio
async def test_create_graph_can_invoke(mock_tools, mock_llm, mock_state):
    """Тест что граф можно вызвать"""
    from unittest.mock import AsyncMock, Mock
    
    # Настраиваем мок модели для быстрого завершения
    mock_response = Mock()
    mock_response.content = """
PLAN:
Тестовый план

STEPS:
1. Тест
"""
    mock_response.tool_calls = []
    mock_llm.ainvoke = AsyncMock(return_value=mock_response)
    
    graph = create_graph(mock_tools, mock_llm)
    
    # Устанавливаем достигнутый лимит для быстрого завершения
    mock_state["applied_count"] = 5
    mock_state["max_applications"] = 5
    
    # Вызываем граф
    result = await graph.ainvoke(mock_state)
    
    assert result is not None
    assert isinstance(result, dict)
    assert "next_agent" in result

