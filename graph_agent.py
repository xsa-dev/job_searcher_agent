"""
Multi-Agent System на базе LangGraph для автоматизации откликов на вакансии HeadHunter

Архитектура:
- Supervisor: главный контроллер, маршрутизирует задачи между агентами
- Planner: создает план работы и адаптирует его на лету на основе истории
- Browser Agent: работает с браузером (логин, поиск, анализ, отклики)
- Cover Letter Agent: генерирует сопроводительные письма

ВНИМАНИЕ: Это обертка для обратной совместимости.
Основная реализация находится в модуле mas/
"""

from __future__ import annotations

import logging

# Импортируем все из модуля mas
from mas import (
    AgentState,
    create_initial_state,
    create_graph,
)

# Импортируем узлы для обратной совместимости с тестами
from mas.supervisor_node import supervisor_node
from mas.planner_node import planner_node
from mas.browser_agent_node import browser_agent_node
from mas.cover_letter_agent_node import cover_letter_agent_node

# Импортируем утилиты для обратной совместимости с тестами
from mas.utils import (
    _format_history_summary,
    _parse_plan,
    _parse_cover_letter,
    _get_successful_letters,
    _check_if_logged_in,
    _get_last_unfinished_plan,
)

# Настройка логирования (для обратной совместимости)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Экспортируем все для обратной совместимости
__all__ = [
    "AgentState",
    "create_initial_state",
    "create_graph",
    "supervisor_node",
    "planner_node",
    "browser_agent_node",
    "cover_letter_agent_node",
    "_format_history_summary",
    "_parse_plan",
    "_parse_cover_letter",
    "_get_successful_letters",
    "_check_if_logged_in",
    "_get_last_unfinished_plan",
]
