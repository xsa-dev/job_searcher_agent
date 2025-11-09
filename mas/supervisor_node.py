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
    
    # Обработка успешной отправки отклика
    elif state["browser_status"] == "application_sent":
        logger.info(f"✅ Отклик отправлен! Прогресс: {state['applied_count']}/{state['max_applications']}")
        
        # Проверяем, достигнут ли лимит откликов
        if state["applied_count"] >= state["max_applications"]:
            logger.info(f"🎯 Достигнут лимит откликов: {state['applied_count']}/{state['max_applications']}")
            state["next_agent"] = "end"
        # Если есть еще вакансии в списке, продолжаем
        elif state["vacancies"] and state["current_vacancy_index"] < len(state["vacancies"]):
            # Выбираем следующую вакансию
            state["current_vacancy"] = state["vacancies"][state["current_vacancy_index"]]
            logger.info(f"📌 Выбрана следующая вакансия {state['current_vacancy_index'] + 1}/{len(state['vacancies'])}: {state['current_vacancy'].get('title', 'N/A')}")
            state["next_agent"] = "cover_letter_agent"
        # Если вакансии закончились, но лимит не достигнут - ищем новые
        elif state["applied_count"] < state["max_applications"]:
            logger.info(f"🔍 Нужно найти больше вакансий ({state['applied_count']}/{state['max_applications']}) → Browser Agent (поиск)")
            # Сбрасываем статус для продолжения поиска
            state["browser_status"] = "logged_in"
            state["next_agent"] = "browser_agent"
        else:
            logger.info("✅ Все отклики отправлены")
            state["next_agent"] = "end"
    
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
    
    elif state["browser_status"] == "vacancies_found" and not state["vacancies"]:
        # Увеличиваем счетчик попыток
        search_attempts = state.get("search_attempts", 0) + 1
        state["search_attempts"] = search_attempts
        
        if search_attempts >= 3:
            logger.warning(f"⚠️ Превышен лимит попыток поиска ({search_attempts}), завершаем работу")
            state["error_message"] = f"Не удалось найти вакансии после {search_attempts} попыток"
            state["browser_status"] = "error"
            state["next_agent"] = "end"
        else:
            logger.info(f"🔍 Вакансии не найдены (попытка {search_attempts}/3), продолжаем поиск → Browser Agent")
            state["browser_status"] = "logged_in"  # Сбрасываем для продолжения поиска
            state["next_agent"] = "browser_agent"
    
    elif state["browser_status"] == "search_failed":
        # Увеличиваем счетчик попыток
        search_attempts = state.get("search_attempts", 0) + 1
        state["search_attempts"] = search_attempts
        
        if search_attempts >= 3:
            logger.warning(f"⚠️ Превышен лимит попыток поиска ({search_attempts}), завершаем работу")
            state["error_message"] = f"Не удалось найти вакансии после {search_attempts} попыток"
            state["browser_status"] = "error"
            state["next_agent"] = "end"
        else:
            logger.info(f"🔍 Поиск не дал результатов (попытка {search_attempts}/3), продолжаем выполнение плана → Browser Agent")
            state["browser_status"] = "logged_in"  # Сбрасываем для продолжения поиска
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

