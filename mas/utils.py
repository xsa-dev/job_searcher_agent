"""
Вспомогательные функции для мультиагентной системы
"""

import logging
import re
from typing import Optional, Tuple

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


def _parse_salary_string(salary_str: str) -> Optional[Tuple[int, Optional[int]]]:
    """
    Парсит строку с зарплатой и возвращает минимальное и максимальное значение.
    
    Обрабатывает форматы:
    - "300 000 ₽ на руки" -> (300000, None)
    - "200000-300000" -> (200000, 300000)
    - "от 200000" -> (200000, None)
    - "до 300000" -> (None, 300000)
    - "200 000 - 300 000 руб." -> (200000, 300000)
    
    Args:
        salary_str: Строка с зарплатой
        
    Returns:
        Tuple (min_salary, max_salary) или None если не удалось распарсить
        Если указана только одна цифра, она считается минимальной
    """
    if not salary_str:
        return None
    
    # Удаляем все пробелы для упрощения парсинга
    salary_clean = salary_str.replace(" ", "").replace("\xa0", "")
    
    # Ищем все числа в строке
    numbers = re.findall(r'\d+', salary_clean)
    
    if not numbers:
        return None
    
    # Конвертируем в int
    salary_values = [int(n) for n in numbers]
    
    # Если одно число - это минимальная зарплата
    if len(salary_values) == 1:
        return (salary_values[0], None)
    
    # Если несколько чисел - первое минимальное, последнее максимальное
    if len(salary_values) >= 2:
        return (salary_values[0], salary_values[-1])
    
    return None


def _extract_desired_salary(resume_data: dict) -> Optional[int]:
    """
    Извлекает желаемую зарплату из данных резюме.
    
    Args:
        resume_data: Словарь с данными резюме
        
    Returns:
        Минимальная желаемая зарплата (int) или None
    """
    desired_salary_str = resume_data.get("desired_salary", "")
    if not desired_salary_str:
        return None
    
    salary_tuple = _parse_salary_string(desired_salary_str)
    if salary_tuple:
        min_salary, _ = salary_tuple
        return min_salary
    
    return None


def _should_skip_vacancy_by_salary(vacancy: dict, desired_salary: Optional[int], threshold: float = 0.8) -> bool:
    """
    Определяет, нужно ли пропустить вакансию из-за низкой зарплаты.
    
    Вакансия пропускается, если:
    - Указана максимальная зарплата в вакансии И она меньше желаемой * threshold
    - Указана только минимальная зарплата в вакансии И она меньше желаемой * threshold
    
    Args:
        vacancy: Словарь с данными вакансии (должен содержать поле 'salary')
        desired_salary: Желаемая минимальная зарплата из резюме
        threshold: Порог (0.8 = 80% от желаемой зарплаты). По умолчанию 0.8
        
    Returns:
        True если нужно пропустить вакансию, False иначе
    """
    if not desired_salary:
        # Если желаемая зарплата не указана, не фильтруем
        return False
    
    vacancy_salary_str = vacancy.get("salary", "")
    if not vacancy_salary_str:
        # Если зарплата в вакансии не указана, не фильтруем
        return False
    
    vacancy_salary = _parse_salary_string(vacancy_salary_str)
    if not vacancy_salary:
        # Не удалось распарсить зарплату, не фильтруем
        return False
    
    min_vacancy, max_vacancy = vacancy_salary
    
    # Определяем максимальную зарплату в вакансии
    # Если указан диапазон - берем максимум
    # Если указана только одна цифра - считаем её минимальной и используем её для сравнения
    if max_vacancy is not None:
        # Есть диапазон - сравниваем максимум
        max_salary_in_vacancy = max_vacancy
    elif min_vacancy is not None:
        # Только одна цифра - используем её как максимальную для сравнения
        max_salary_in_vacancy = min_vacancy
    else:
        # Не удалось определить зарплату
        return False
    
    # Сравниваем: если максимальная зарплата в вакансии меньше желаемой * threshold - пропускаем
    threshold_salary = desired_salary * threshold
    
    if max_salary_in_vacancy < threshold_salary:
        logger.info(
            f"   💰 Вакансия '{vacancy.get('title', 'N/A')}' пропущена по зарплате: "
            f"в вакансии до {max_salary_in_vacancy} ₽, желаемая {desired_salary} ₽ "
            f"(порог {threshold_salary:.0f} ₽)"
        )
        return True
    
    return False

