"""
Создание и компиляция графа мультиагентной системы
"""

import logging

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from .state import AgentState
from .supervisor_node import supervisor_node
from .planner_node import planner_node
from .browser_agent_node import browser_agent_node
from .cover_letter_agent_node import cover_letter_agent_node
from .tools import wait_tool_instance

logger = logging.getLogger(__name__)


def create_graph(mcp_tools: list, model: ChatOpenAI) -> StateGraph:
    """Создает и компилирует граф мультиагентной системы"""
    logger.info("🏗️ Создание графа мультиагентной системы")
    
    # Добавляем wait tool к MCP tools
    all_tools = list(mcp_tools) + [wait_tool_instance]
    
    # Создаем граф
    workflow = StateGraph(AgentState)
    
    # Добавляем узлы
    # Supervisor - синхронный
    workflow.add_node("supervisor", supervisor_node)
    
    # Остальные узлы - асинхронные, нужно создать обертки
    async def planner_wrapper(state: AgentState) -> AgentState:
        return await planner_node(state, model, all_tools)
    
    async def browser_wrapper(state: AgentState) -> AgentState:
        return await browser_agent_node(state, model, all_tools)
    
    async def cover_letter_wrapper(state: AgentState) -> AgentState:
        return await cover_letter_agent_node(state, model, all_tools)
    
    workflow.add_node("planner", planner_wrapper)
    workflow.add_node("browser_agent", browser_wrapper)
    workflow.add_node("cover_letter_agent", cover_letter_wrapper)
    
    # Точка входа
    workflow.set_entry_point("supervisor")
    
    # Условные переходы от supervisor
    def supervisor_router(state: AgentState) -> str:
        return state["next_agent"]
    
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "planner": "planner",
            "browser_agent": "browser_agent",
            "cover_letter_agent": "cover_letter_agent",
            "end": END
        }
    )
    
    # После каждого агента возвращаемся к supervisor
    workflow.add_edge("planner", "supervisor")
    workflow.add_edge("browser_agent", "supervisor")
    workflow.add_edge("cover_letter_agent", "supervisor")
    
    logger.info("✅ Граф создан успешно")
    
    return workflow.compile()