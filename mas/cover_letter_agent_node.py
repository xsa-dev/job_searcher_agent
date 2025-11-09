"""
Cover Letter Agent node - генерация сопроводительных писем
"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage

from .state import AgentState
from .prompts import COVER_LETTER_AGENT_PROMPT
from .utils import _parse_cover_letter, _get_successful_letters
from .chroma_utils import (
    get_similar_cover_letters,
    store_cover_letter,
    format_chroma_results,
)

logger = logging.getLogger(__name__)


async def cover_letter_agent_node(state: AgentState, model: ChatOpenAI, tools: list = None) -> AgentState:
    """Cover Letter Agent генерирует сопроводительное письмо"""
    logger.info("=" * 80)
    logger.info("✍️ COVER LETTER AGENT: Генерация письма")
    logger.info("=" * 80)
    
    vacancy = state["current_vacancy"]
    resume_data = state["resume_data"]
    
    # Получаем примеры успешных писем из истории
    successful_examples = _get_successful_letters(state["previous_sessions"])
    
    # Если Chroma включен, ищем дополнительные примеры из векторного хранилища
    if state.get("chroma_enabled", False) and tools:
        from .chroma_utils import get_chroma_tools
        chroma_tools = get_chroma_tools(tools)
        
        if chroma_tools:
            logger.info("🔍 Поиск похожих писем в Chroma...")
            similar_letters = await get_similar_cover_letters(
                chroma_tools,
                vacancy,
                n_results=3,
                only_successful=True
            )
            
            if similar_letters and similar_letters.get("documents"):
                logger.info(f"✅ Найдено {len(similar_letters['documents'][0])} похожих писем в Chroma")
                chroma_examples = format_chroma_results(similar_letters)
                successful_examples += f"\n\n--- Примеры из Chroma ---\n{chroma_examples}"
            else:
                logger.info("ℹ️ Похожих писем в Chroma не найдено")
    
    # Формируем строку с опытом работы
    work_history_text = ""
    work_history = resume_data.get("work_history", [])
    if work_history:
        # Берем последние 3-4 позиции (самые релевантные)
        recent_jobs = work_history[:4]
        work_history_lines = []
        for job in recent_jobs:
            job_text = f"- {job.get('position', 'N/A')} в {job.get('company', 'N/A')}"
            if job.get('period'):
                job_text += f" ({job.get('period')})"
            if job.get('location'):
                job_text += f", {job.get('location')}"
            work_history_lines.append(job_text)
            
            # Добавляем ключевые достижения (первые 2-3)
            achievements = job.get("achievements", [])[:3]
            if achievements:
                for achievement in achievements:
                    work_history_lines.append(f"  • {achievement}")
        work_history_text = "\n".join(work_history_lines)
    else:
        work_history_text = "Опыт работы не указан"
    
    # Формируем строку с ключевыми достижениями
    key_achievements = []
    for job in work_history[:3]:  # Берем из последних 3 позиций
        achievements = job.get("achievements", [])
        key_achievements.extend(achievements[:2])  # По 2 достижения из каждой позиции
    
    key_achievements_text = "\n".join([f"- {ach}" for ach in key_achievements[:6]]) if key_achievements else "Ключевые достижения не указаны"
    
    # Формируем полное имя
    full_name = resume_data.get("full_name", resume_data.get("title", "Кандидат"))

    name = resume_data.get("full_name", "Алексей Савин")
    email = resume_data.get("email", "saleksey67@gmail.com")
    phone = resume_data.get("phone", "+79166705363")
    linkedin = resume_data.get("linkedin", "https://www.linkedin.com/in/alxy-dev/")
    github = resume_data.get("github", "https://github.com/xsa-dev")
    portfolio = resume_data.get("portfolio", "Мой портфолио:")
    portfolio_url = resume_data.get("portfolio_url", "https://prometheusai-labs.github.io/")
    portfolio_url_text = resume_data.get("portfolio_url_text", "prometheusai-labs.github.io")

    prompt = COVER_LETTER_AGENT_PROMPT.format(
        resume_full_name=full_name,
        resume_title=resume_data.get("title", ""),
        resume_experience=resume_data.get("work_experience", "Не указан"),
        resume_tags=", ".join(resume_data.get("tags", [])),
        resume_summary=resume_data.get("summary", resume_data.get("about_me", "")),
        resume_work_history=work_history_text,
        resume_key_achievements=key_achievements_text[:200],
        vacancy_title=vacancy.get("title", ""),
        vacancy_company=vacancy.get("company", ""),
        vacancy_description=vacancy.get("description", ""),
        vacancy_requirements=vacancy.get("requirements", "")[:200],
        vacancy_score=vacancy.get("score", 0.0),
        successful_letters_examples=successful_examples,
        name=name,
        email=email,
        phone=phone,
        linkedin=linkedin,
        github=github,
        portfolio=portfolio,
        portfolio_url=portfolio_url,
        portfolio_url_text=portfolio_url_text,
    )

    card = f"""
Алексей Савин
saleksey67@gmail.com
+79166705363
LinkedIn: https://www.linkedin.com/in/alxy-dev/
GitHub: https://github.com/xsa-dev
Портфолио: Мой портфолио - https://prometheusai-labs.github.io/
"""

    prompt = prompt.replace("[ИМЯ]", card)
    
    # ОГРАНИЧЕНИЕ: Минимизируем контекст для экономии токенов
    messages = [SystemMessage(content=prompt)]
    response = await model.ainvoke(messages)
    
    # Парсим письмо
    cover_letter = _parse_cover_letter(response.content)
    state["cover_letter"] = cover_letter

    cover_letter = cover_letter.replace("[ИМЯ]", name)
    
    logger.info(f"✅ Письмо создано ({len(cover_letter)} символов)")
    logger.info(f"Превью: {cover_letter[:200]}...")
    
    # Сохраняем письмо в Chroma если включен
    if state.get("chroma_enabled", False) and tools:
        from .chroma_utils import get_chroma_tools
        chroma_tools = get_chroma_tools(tools)
        
        if chroma_tools:
            logger.info("💾 Сохранение сопроводительного письма в Chroma...")
            await store_cover_letter(
                chroma_tools,
                vacancy,
                cover_letter,
                state["session_id"],
                was_successful=False  # Пока не знаем, будет обновлено после отклика
            )
            logger.info("✅ Письмо сохранено в Chroma")
    
    return state

