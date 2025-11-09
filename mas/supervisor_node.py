"""
Supervisor node - главный контроллер мультиагентной системы
"""

import logging

from .state import AgentState

logger = logging.getLogger(__name__)


def supervisor_node(state: AgentState) -> AgentState:
    """Supervisor анализирует состояние и решает, какому агенту передать управление"""
    logger.info("=" * 80)
    logger.info("🎯 SUPERVISOR: Анализ текущего состояния")
    logger.info("=" * 80)
    
    # Проверяем условия завершения
    if state["applied_count"] >= state["max_applications"]:
        logger.info(f"✅ Достигнут лимит откликов: {state['applied_count']}/{state['max_applications']}")
        state["next_agent"] = "end"
        return state
    
    if state["browser_status"] == "error" and state["error_message"]:
        logger.error(f"❌ Критическая ошибка браузера: {state['error_message']}")
        state["next_agent"] = "end"
        return state
    
    # Определяем следующего агента
    if not state["plan"] or state["plan_needs_update"]:
        logger.info("📋 План отсутствует или требует обновления → Planner")
        state["next_agent"] = "planner"
    
    elif state["vacancies"] and state["current_vacancy_index"] >= len(state["vacancies"]):
        # Все вакансии обработаны
        logger.info("✅ Все вакансии обработаны")
        state["next_agent"] = "end"
    
    elif not state["browser_session_active"] or state["browser_status"] == "idle":
        logger.info("🌐 Браузер не активен → Browser Agent (логин)")
        state["next_agent"] = "browser_agent"
    
    elif state["browser_status"] == "logged_in" and not state["vacancies"]:
        logger.info("🔍 Нужно найти вакансии → Browser Agent (поиск)")
        state["next_agent"] = "browser_agent"
    
    elif state["vacancies"] and not state["current_vacancy"]:
        # Выбираем следующую вакансию
        if state["current_vacancy_index"] < len(state["vacancies"]):
            state["current_vacancy"] = state["vacancies"][state["current_vacancy_index"]]
            logger.info(f"📌 Выбрана вакансия {state['current_vacancy_index'] + 1}/{len(state['vacancies'])}: {state['current_vacancy'].get('title')}")
            state["next_agent"] = "cover_letter_agent"
        else:
            logger.info("✅ Все вакансии обработаны")
            state["next_agent"] = "end"
    
    elif state["current_vacancy"] and not state["cover_letter"]:
        logger.info("✍️ Нужно создать письмо → Cover Letter Agent")
        state["next_agent"] = "cover_letter_agent"
    
    elif state["current_vacancy"] and state["cover_letter"]:
        logger.info("📤 Готово к отклику → Browser Agent (отклик)")
        state["next_agent"] = "browser_agent"
    
    else:
        logger.warning("⚠️ Неопределенное состояние, завершаем работу")
        state["next_agent"] = "end"
    
    logger.info(f"➡️ Следующий агент: {state['next_agent']}")
    return state

