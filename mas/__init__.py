"""
Multi-Agent System (MAS) для автоматизации откликов на вакансии HeadHunter

Модульная структура мультиагентной системы на базе LangGraph.
"""

from .state import AgentState, create_initial_state
from .graph import create_graph

# Экспортируем основные компоненты
__all__ = [
    "AgentState",
    "create_initial_state",
    "create_graph",
]

