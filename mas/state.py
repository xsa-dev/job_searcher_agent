"""
Определение состояния мультиагентной системы (AgentState)
"""

from __future__ import annotations

import time
from typing import Annotated, TypedDict, Optional

from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    """Состояние мультиагентной системы"""
    
    # Сообщения между агентами и LLM
    messages: Annotated[list[BaseMessage], add_messages]
    
    # Основная информация о задаче
    user_request: str
    session_id: str
    start_time: float
    
    # План работы
    plan: str
    plan_steps: list[str]
    current_step: int
    plan_needs_update: bool
    
    # Данные о резюме
    resume_data: dict
    hh_login: str
    hh_password: str
    
    # Вакансии
    vacancies: list[dict]  # все найденные вакансии
    current_vacancy: Optional[dict]  # текущая обрабатываемая
    current_vacancy_index: int
    use_recommended: bool  # использовать рекомендованные вакансии вместо поиска
    processed_vacancies: list[dict]  # вакансии с полной информацией о результате отклика
    
    # Сопроводительное письмо
    cover_letter: str
    
    # Статистика
    applied_count: int
    max_applications: int
    rejected_count: int
    search_attempts: int  # Количество попыток поиска вакансий
    
    # Статус браузера и агентов
    browser_status: str  # "idle", "logged_in", "vacancies_found", "application_sent", "error", "search_failed"
    browser_session_active: bool
    
    # История предыдущих сессий
    previous_sessions: list[dict]
    already_applied_urls: set[str]
    
    # Маршрутизация
    next_agent: str  # "planner", "browser_agent", "cover_letter_agent", "end"
    
    # Chroma интеграция
    chroma_enabled: bool  # Включен ли Chroma
    chroma_collections_ready: bool  # Готовы ли коллекции
    vacancies_indexed: int  # Количество проиндексированных вакансий
    
    # Ошибки
    error_message: str


def create_initial_state(
    user_request: str,
    resume_data: dict,
    hh_login: str,
    hh_password: str,
    max_applications: int = 5,
    previous_sessions: list[dict] = None,
    already_applied_urls: set[str] = None,
    use_recommended: bool = False,
    chroma_enabled: bool = True
) -> AgentState:
    """
    Создает начальное состояние для графа
    
    Args:
        use_recommended: Если True, использовать рекомендованные вакансии с главной страницы
                        вместо детального поиска. Экономит время (~30-60 сек).
        chroma_enabled: Включить ли интеграцию с Chroma для векторного поиска
    """
    
    return AgentState(
        messages=[],
        user_request=user_request,
        session_id=f"session_{int(time.time())}",
        start_time=time.time(),
        plan="",
        plan_steps=[],
        current_step=0,
        plan_needs_update=False,
        resume_data=resume_data,
        hh_login=hh_login,
        hh_password=hh_password,
        vacancies=[],
        current_vacancy=None,
        current_vacancy_index=0,
        use_recommended=use_recommended,
        processed_vacancies=[],
        cover_letter="",
        applied_count=0,
        max_applications=max_applications,
        rejected_count=0,
        search_attempts=0,
        browser_status="idle",
        browser_session_active=False,
        previous_sessions=previous_sessions or [],
        already_applied_urls=already_applied_urls or set(),
        next_agent="planner",
        chroma_enabled=chroma_enabled,
        chroma_collections_ready=False,
        vacancies_indexed=0,
        error_message=""
    )

