"""
Planner node - создание и адаптация плана работы
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from .state import AgentState
from .prompts import PLANNER_PROMPT
from .utils import _format_history_summary, _parse_plan, _get_last_unfinished_plan
from .chroma_utils import (
    get_chroma_tools,
    get_vacancy_history,
    store_resume_skills,
    format_chroma_results,
)

logger = logging.getLogger(__name__)


async def planner_node(state: AgentState, model: ChatOpenAI, tools: list = None) -> AgentState:
    """Planner создает и адаптирует план работы"""
    logger.info("=" * 80)
    logger.info("📋 PLANNER: Создание/адаптация плана")
    logger.info("=" * 80)
    
    # Инициализация Chroma если включен
    chroma_history = ""
    if state.get("chroma_enabled", False) and tools:
        logger.info("🔧 Инициализация Chroma для анализа истории...")
        chroma_tools = get_chroma_tools(tools)
        
        if chroma_tools:
            # Индексируем навыки из резюме если еще не сделано
            resume_data = state.get("resume_data", {})
            logger.info("📝 Индексация навыков резюме в Chroma...")
            await store_resume_skills(chroma_tools, resume_data)
            
            # Ищем историю успешных вакансий для аналогичной позиции
            resume_title = resume_data.get("title", "")
            if resume_title:
                logger.info(f"🔍 Поиск истории вакансий для '{resume_title}'...")
                vacancy_history = await get_vacancy_history(
                    chroma_tools,
                    resume_title,
                    n_results=5
                )
                
                if vacancy_history and vacancy_history.get("documents"):
                    logger.info(f"✅ Найдено {len(vacancy_history['documents'][0])} вакансий в истории Chroma")
                    chroma_history = format_chroma_results(vacancy_history)
                else:
                    logger.info("ℹ️ История вакансий в Chroma пока пуста")
    
    # Проверяем, есть ли невыполненный план в истории
    last_unfinished_plan = _get_last_unfinished_plan(state["previous_sessions"])
    
    if last_unfinished_plan and not state["plan_needs_update"]:
        # Используем последний невыполненный план
        logger.info("♻️ Найден невыполненный план из предыдущей сессии")
        state["plan"] = last_unfinished_plan["plan"]
        state["plan_steps"] = last_unfinished_plan["plan_steps"]
        state["plan_needs_update"] = False
        state["current_step"] = 0
        
        logger.info(f"✅ План загружен из истории: {len(state['plan_steps'])} шагов")
        logger.info(f"План:\n{state['plan']}")
        return state
    
    # Если нет невыполненного плана или требуется обновление - создаем новый
    logger.info("🆕 Создание нового плана...")
    
    # Подготавливаем данные для промпта
    resume_data = state.get("resume_data", {})
    history_summary = _format_history_summary(state["previous_sessions"])
    
    # Добавляем данные из Chroma если доступны
    if chroma_history:
        history_summary += f"\n\n--- История из Chroma (семантический поиск) ---\n{chroma_history}"
    
    prompt = PLANNER_PROMPT.format(
        user_request=state["user_request"],
        resume_title=resume_data.get("title", "Не указано"),
        resume_tags=", ".join(resume_data.get("tags", [])),
        resume_summary=resume_data.get("summary", "Не указано")[:200],
        sessions_count=len(state["previous_sessions"]),
        history_summary=history_summary,
        applied_count=state["applied_count"],
        max_applications=state["max_applications"],
        vacancies_count=len(state["vacancies"]),
        already_applied_count=len(state["already_applied_urls"])
    )
    
    # Вызываем LLM
    # ОГРАНИЧЕНИЕ: Минимизируем контекст для экономии токенов
    messages = [SystemMessage(content=prompt)]
    response = await model.ainvoke(messages)
    
    # Парсим ответ
    plan_text = response.content
    plan, steps = _parse_plan(plan_text)
    
    state["plan"] = plan
    state["plan_steps"] = steps
    state["plan_needs_update"] = False
    state["current_step"] = 0
    
    logger.info(f"✅ План создан: {len(steps)} шагов")
    logger.info(f"План:\n{plan}")
    
    return state

