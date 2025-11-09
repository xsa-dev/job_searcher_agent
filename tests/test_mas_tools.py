"""
Тесты для mas/tools.py
"""

import pytest
import time
from mas.tools import wait_tool, wait_tool_instance, WaitInput


def test_wait_tool_default():
    """Тест wait_tool с параметром по умолчанию"""
    start = time.time()
    result = wait_tool()
    elapsed = time.time() - start
    
    assert isinstance(result, str)
    assert "3.0" in result or "3" in result
    assert elapsed >= 3.0
    assert elapsed < 3.5  # С запасом на погрешность


def test_wait_tool_custom_seconds():
    """Тест wait_tool с кастомным временем"""
    start = time.time()
    result = wait_tool(seconds=1.0)
    elapsed = time.time() - start
    
    assert "1.0" in result or "1" in result
    assert elapsed >= 1.0
    assert elapsed < 1.5


def test_wait_tool_returns_string():
    """Тест что wait_tool возвращает строку"""
    result = wait_tool(seconds=0.1)
    
    assert isinstance(result, str)
    assert "Ожидание завершено" in result


def test_wait_input_schema():
    """Тест схемы WaitInput"""
    wait_input = WaitInput()
    
    assert hasattr(wait_input, 'seconds')
    assert wait_input.seconds == 3.0


def test_wait_input_custom_value():
    """Тест WaitInput с кастомным значением"""
    wait_input = WaitInput(seconds=5.0)
    
    assert wait_input.seconds == 5.0


def test_wait_tool_instance_structure():
    """Тест структуры wait_tool_instance"""
    assert hasattr(wait_tool_instance, 'name')
    assert hasattr(wait_tool_instance, 'description')
    assert hasattr(wait_tool_instance, 'func')
    
    assert wait_tool_instance.name == "wait"
    assert "секунд" in wait_tool_instance.description.lower() or "seconds" in wait_tool_instance.description.lower()


def test_wait_tool_instance_callable():
    """Тест что wait_tool_instance можно вызвать"""
    result = wait_tool_instance.func(seconds=0.1)
    
    assert isinstance(result, str)
    assert "0.1" in result


def test_wait_tool_zero_seconds():
    """Тест wait_tool с нулевым временем"""
    start = time.time()
    result = wait_tool(seconds=0.0)
    elapsed = time.time() - start
    
    assert isinstance(result, str)
    assert elapsed < 0.5  # Должно быть быстро

