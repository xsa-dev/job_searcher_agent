"""
Вспомогательные функции для мультиагентной системы
"""

import logging
from typing import Optional

from .state import AgentState

logger = logging.getLogger(__name__)


def _format_history_summary(sessions: list[dict]) -> str:
    """Форматирует историю сессий для промпта с минимальным использованием токенов"""
    if not sessions:
        return "История отсутствует"
    
    summary_parts = []
    # Ограничиваем только последними 2 сессиями для экономии токенов
    for i, session in enumerate(sessions[-2:], 1):
        stats = session.get("statistics", {})
        summary_parts.append(
            f"Сессия {i}: {stats.get('total_applied', 0)} откликов, "
            f"средний score {stats.get('average_score', 0.0):.1f}, "
            f"найдено {stats.get('total_vacancies_found', 0)} вакансий"
        )
    
    return " | ".join(summary_parts)


def _parse_plan(plan_text: str) -> tuple[str, list[str]]:
    """Парсит план из ответа LLM"""
    lines = plan_text.split("\n")
    plan = ""
    steps = []
    
    in_plan = False
    in_steps = False
    
    for line in lines:
        if "PLAN:" in line:
            in_plan = True
            in_steps = False
            continue
        elif "STEPS:" in line:
            in_steps = True
            in_plan = False
            continue
        
        if in_plan:
            plan += line + "\n"
        elif in_steps and line.strip():
            # Удаляем номер шага если есть
            step = line.strip()
            if step and (step[0].isdigit() or step.startswith("-")):
                step = step.split(".", 1)[-1].split(")", 1)[-1].strip()
            if step:
                steps.append(step)
    
    return plan.strip(), steps


def _parse_cover_letter(response: str) -> str:
    """Парсит сопроводительное письмо из ответа LLM"""
    if "COVER_LETTER:" in response:
        return response.split("COVER_LETTER:", 1)[1].strip()
    return response.strip()


def _get_successful_letters(sessions: list[dict]) -> str:
    """Извлекает примеры успешных писем из истории - минимальный формат для экономии токенов"""
    examples = []
    for session in sessions[-1:]:  # Только последняя сессия
        vacancies = session.get("vacancies_processed", [])
        for vacancy in vacancies:
            if vacancy.get("applied") and vacancy.get("score", 0) > 0.7:
                examples.append(
                    f"Вакансия '{vacancy.get('title', 'N/A')}', score {vacancy.get('score', 0):.1f}: "
                    f"{vacancy.get('cover_letter', '')[:100]}..."
                )
                if len(examples) >= 1:  # Только 1 пример
                    break
        if len(examples) >= 1:
            break
    
    return " | ".join(examples) if examples else "Примеров пока нет"


async def _check_if_logged_in(tools_by_name: dict) -> bool:
    """
    Проверяет, авторизован ли пользователь на HeadHunter
    
    Проверяет наличие специфичных элементов меню HH:
    - "Резюме" / "Профиль"
    - "Отклики"
    - Иконки сообщений
    - Иконки нотификаций
    
    Returns:
        True если пользователь авторизован, False иначе
    """
    try:
        # Получаем snapshot страницы
        if "playwright_get_visible_text" in tools_by_name:
            snapshot_tool = tools_by_name["playwright_get_visible_text"]
            snapshot_result = await snapshot_tool.ainvoke({})
            page_content = str(snapshot_result).lower()
        elif "playwright_get_visible_html" in tools_by_name:
            snapshot_tool = tools_by_name["playwright_get_visible_html"]
            snapshot_result = await snapshot_tool.ainvoke({})
            page_content = str(snapshot_result).lower()
            
            # Специфичные признаки авторизации на HH (пункты меню)
            logged_in_indicators = [
                "резюме",           # Пункт меню "Резюме"
                "профиль",          # Пункт меню "Профиль"
                "отклики",          # Пункт меню "Отклики"
                "сообщения",        # Иконка сообщений
                "уведомления",      # Иконка уведомлений
                "notifications",    # Notifications (англ.)
                "messages",         # Messages (англ.)
                "responses",        # Responses (англ.)
            ]
            
            # Признаки НЕавторизации (кнопка входа)
            not_logged_in_indicators = [
                "войти",
                "вход",
                "sign in",
                "log in",
            ]
            
            # Подсчитываем совпадения
            found_indicators = []
            for indicator in logged_in_indicators:
                if indicator in page_content:
                    found_indicators.append(indicator)
            
            not_logged_in_count = sum(1 for indicator in not_logged_in_indicators if indicator in page_content)
            
            logger.info(f"   Найдено элементов авторизованного меню: {len(found_indicators)}")
            if found_indicators:
                logger.info(f"   Найденные элементы: {', '.join(found_indicators[:5])}")
            logger.info(f"   Признаков НЕавторизации: {not_logged_in_count}")
            
            # Если найдено хотя бы 2 элемента из меню авторизованного пользователя
            # И нет явных признаков неавторизации - считаем что залогинен
            if len(found_indicators) >= 2 and not_logged_in_count == 0:
                return True
            
            # Если найдено 3+ элемента - точно авторизован, даже если есть кнопка "Войти"
            if len(found_indicators) >= 3:
                return True
            
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка проверки авторизации: {e}")
        return False


def _get_last_unfinished_plan(sessions: list[dict]) -> Optional[dict]:
    """
    Ищет последний невыполненный план в истории сессий
    
    Невыполненный план - это план из последней сессии, если:
    - В ней есть план и шаги
    - План похож на текущий запрос (для одной и той же задачи)
    
    Returns:
        dict с ключами 'plan' и 'plan_steps' или None
    """
    if not sessions:
        logger.info("📭 История сессий пуста")
        return None
    
    # Берем последнюю сессию
    last_session = sessions[-1]
    
    plan = last_session.get("plan", "")
    plan_steps = last_session.get("plan_steps", [])
    
    logger.info(f"🔍 Проверка последней сессии: {last_session.get('timestamp')}")
    logger.info(f"   План: {'есть' if plan else 'нет'} ({len(plan)} символов)")
    logger.info(f"   Шаги: {len(plan_steps)} шагов")
    
    # Если есть план и шаги - используем их
    if plan and plan_steps and len(plan) > 50:
        stats = last_session.get("statistics", {})
        total_applied = stats.get("total_applied", 0)
        total_found = stats.get("total_vacancies_found", 0)
        
        logger.info("♻️ Найден план из предыдущей сессии")
        logger.info(f"   Откликов было: {total_applied}/{total_found}")
        logger.info("   Переиспользуем план для продолжения работы")
        
        return {
            "plan": plan,
            "plan_steps": plan_steps
        }
    
    logger.info("❌ Подходящий план не найден, нужно создать новый")
    return None

