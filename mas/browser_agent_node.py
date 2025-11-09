"""
Browser Agent node - работа с браузером
"""

import logging
from typing import List

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, ToolMessage, AIMessage, BaseMessage

from .state import AgentState
from .prompts import BROWSER_AGENT_PROMPT
from .utils import _check_if_logged_in
from .chroma_utils import (
    get_chroma_tools,
    ensure_collections_exist,
    store_vacancy,
    check_vacancy_duplicate,
)

logger = logging.getLogger(__name__)

# Константы для ограничения размера контекста
MAX_MESSAGES_HISTORY = 30  # Максимум сообщений в истории для модели
MAX_TOOL_RESULT_SIZE = 5000  # Максимум символов в результате обычного инструмента
MAX_SNAPSHOT_SIZE = 10000  # Максимум символов для browser_snapshot
MAX_HTML_SIZE = 8000  # Максимум символов для HTML результатов


def _truncate_messages(messages: List[BaseMessage], max_messages: int = MAX_MESSAGES_HISTORY) -> List[BaseMessage]:
    """
    Обрезает историю сообщений, оставляя только последние N сообщений.
    Сохраняет системные сообщения и последние итерации ReAct цикла.
    ВАЖНО: Не оставляет ToolMessage без предшествующего AIMessage с tool_calls.
    
    Args:
        messages: Полная история сообщений
        max_messages: Максимальное количество сообщений для сохранения
        
    Returns:
        Обрезанный список сообщений с сохраненной целостностью последовательности
    """
    if len(messages) <= max_messages:
        return messages
    
    # Разделяем сообщения на системные и остальные
    system_messages = [msg for msg in messages if isinstance(msg, SystemMessage)]
    other_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
    
    # Если остальных сообщений меньше лимита, возвращаем все
    if len(other_messages) <= max_messages:
        return messages
    
    # Начинаем с конца и собираем сообщения, сохраняя целостность
    # Если первое сообщение в обрезанном списке - ToolMessage, нужно включить предшествующий AIMessage
    start_idx = max(0, len(other_messages) - max_messages)
    
    # Проверяем, что первое сообщение не является ToolMessage без предшествующего AIMessage
    if start_idx > 0 and isinstance(other_messages[start_idx], ToolMessage):
        # Ищем предшествующий AIMessage с соответствующим tool_call
        found_ai = False
        for j in range(start_idx - 1, -1, -1):
            prev_msg = other_messages[j]
            if isinstance(prev_msg, AIMessage) and hasattr(prev_msg, 'tool_calls') and prev_msg.tool_calls:
                tool_call_ids = {tc.get("id") for tc in prev_msg.tool_calls if isinstance(tc, dict)}
                if other_messages[start_idx].tool_call_id in tool_call_ids:
                    # Начинаем с AIMessage
                    start_idx = j
                    found_ai = True
                    break
        
        if not found_ai:
            # Если не нашли предшествующий AIMessage, пропускаем этот ToolMessage
            logger.warning("⚠️ Пропущен ToolMessage без предшествующего AIMessage с tool_calls")
            start_idx += 1
    
    # Обрезаем список
    truncated_other = other_messages[start_idx:]
    
    # Объединяем системные сообщения с обрезанными
    result = system_messages + truncated_other
    
    # Логируем обрезку
    removed_count = len(messages) - len(result)
    logger.debug(f"✂️ Обрезано {removed_count} сообщений из истории (было {len(messages)}, стало {len(result)})")
    
    return result


def _truncate_tool_result(result: str, tool_name: str) -> str:
    """
    Обрезает большие результаты инструментов до разумного размера.
    
    Args:
        result: Результат выполнения инструмента
        tool_name: Название инструмента
        
    Returns:
        Обрезанный результат с указанием обрезки
    """
    result_str = str(result)
    
    # Определяем лимит в зависимости от типа инструмента
    if "snapshot" in tool_name.lower():
        max_size = MAX_SNAPSHOT_SIZE
    elif "html" in tool_name.lower() or "visible_html" in tool_name.lower():
        max_size = MAX_HTML_SIZE
    elif "visible_text" in tool_name.lower():
        max_size = MAX_TOOL_RESULT_SIZE
    else:
        max_size = MAX_TOOL_RESULT_SIZE
    
    if len(result_str) <= max_size:
        return result_str
    
    # Обрезаем и добавляем указание об обрезке
    truncated = result_str[:max_size]
    original_size = len(result_str)
    
    logger.debug(f"✂️ Обрезан результат {tool_name}: {original_size} → {max_size} символов")
    
    return f"{truncated}\n\n[Контент обрезан: было {original_size} символов, оставлено {max_size}]"


def _detect_application_sequence(messages: List) -> bool:
    """
    Отслеживает последовательность вызовов инструментов для определения успешного отклика.
    
    Ищет паттерн:
    1. browser_click с "Откликнуться" или "Respond"
    2. browser_type с текстом письма (длина > 50 символов)
    3. browser_click с "Отправить", "Send", или просто button click после type
    
    Args:
        messages: История сообщений с агентом
        
    Returns:
        True если найдена полная последовательность отклика
    """
    # Ищем последние несколько сообщений (последние 20)
    recent_messages = messages[-20:] if len(messages) > 20 else messages
    
    found_respond_click = False
    found_letter_type = False
    found_submit_click = False
    
    for msg in recent_messages:
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_args = tool_call.get("args", {})
                
                # Шаг 1: Клик на "Откликнуться"
                if tool_name == "browser_click" and not found_respond_click:
                    element = str(tool_args.get("element", "")).lower()
                    if any(word in element for word in ["откликнуться", "respond", "отклик"]):
                        found_respond_click = True
                        logger.debug("   🔍 Найден клик на 'Откликнуться'")
                
                # Шаг 2: Ввод текста письма
                elif tool_name == "browser_type" and found_respond_click and not found_letter_type:
                    text = str(tool_args.get("text", ""))
                    # Проверяем что это письмо (длина > 50 символов)
                    if len(text) > 50:
                        found_letter_type = True
                        logger.debug(f"   🔍 Найден ввод письма ({len(text)} символов)")
                
                # Шаг 3: Клик на кнопку отправки
                elif tool_name == "browser_click" and found_respond_click and found_letter_type:
                    element = str(tool_args.get("element", "")).lower()
                    # Кнопка отправки может называться по-разному
                    if any(word in element for word in ["отправить", "send", "откликнуться", "submit"]):
                        found_submit_click = True
                        logger.debug("   🔍 Найден клик на 'Отправить'")
                        break
        
        # Если нашли все три шага, можно прерывать
        if found_respond_click and found_letter_type and found_submit_click:
            break
    
    # Результат
    if found_respond_click and found_letter_type and found_submit_click:
        logger.info("✅ Обнаружена полная последовательность отклика!")
        return True
    else:
        logger.debug(f"   ❌ Последовательность неполная: respond={found_respond_click}, type={found_letter_type}, submit={found_submit_click}")
        return False


async def _parse_vacancy_details(tools_by_name: dict, current_vacancy: dict) -> dict:
    """
    Парсит детали вакансии через browser_snapshot.
    
    Извлекает:
    - title: название вакансии
    - company: название компании
    - salary: зарплата (если указана)
    - location: локация
    - url: текущий URL страницы
    
    Args:
        tools_by_name: Словарь доступных инструментов
        current_vacancy: Текущая вакансия (может быть неполной)
        
    Returns:
        Обновленный словарь с информацией о вакансии
    """
    vacancy_info = current_vacancy.copy() if current_vacancy else {}
    
    try:
        # Получаем snapshot страницы
        if "browser_snapshot" in tools_by_name:
            snapshot_tool = tools_by_name["browser_snapshot"]
            snapshot_result = await snapshot_tool.ainvoke({})
            page_content = str(snapshot_result)
            
            logger.debug(f"📸 Получен snapshot страницы ({len(page_content)} символов)")
            
            # Простой парсинг на основе типичной структуры HeadHunter
            # Ищем заголовок вакансии (обычно в h1 или data-qa="vacancy-title")
            import re
            
            # Название вакансии
            if not vacancy_info.get("title"):
                # Ищем паттерны типа "вакансия", "vacancy" в заголовках
                title_match = re.search(r'vacancy.*?heading.*?["\']([^"\']+)["\']', page_content, re.IGNORECASE)
                if title_match:
                    vacancy_info["title"] = title_match.group(1).strip()
                    logger.debug(f"   📝 Найдено название: {vacancy_info['title'][:50]}")
            
            # Компания
            if not vacancy_info.get("company"):
                company_match = re.search(r'company.*?name.*?["\']([^"\']+)["\']', page_content, re.IGNORECASE)
                if not company_match:
                    company_match = re.search(r'employer.*?["\']([^"\']+)["\']', page_content, re.IGNORECASE)
                if company_match:
                    vacancy_info["company"] = company_match.group(1).strip()
                    logger.debug(f"   🏢 Найдена компания: {vacancy_info['company'][:50]}")
            
            # Зарплата
            if not vacancy_info.get("salary"):
                salary_match = re.search(r'salary.*?["\']([^"\']*\d+[^"\']*)["\']', page_content, re.IGNORECASE)
                if salary_match:
                    vacancy_info["salary"] = salary_match.group(1).strip()
                    logger.debug(f"   💰 Найдена зарплата: {vacancy_info['salary']}")
            
            # Локация
            if not vacancy_info.get("location"):
                location_match = re.search(r'location.*?["\']([^"\']+)["\']', page_content, re.IGNORECASE)
                if not location_match:
                    location_match = re.search(r'address.*?city.*?["\']([^"\']+)["\']', page_content, re.IGNORECASE)
                if location_match:
                    vacancy_info["location"] = location_match.group(1).strip()
                    logger.debug(f"   📍 Найдена локация: {vacancy_info['location']}")
            
            logger.info(f"✅ Информация о вакансии обновлена: {len(vacancy_info)} полей")
            
        else:
            logger.warning("⚠️ browser_snapshot недоступен, пропускаем парсинг")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при парсинге вакансии: {e}")
    
    return vacancy_info


async def browser_agent_node(state: AgentState, model: ChatOpenAI, tools: list) -> AgentState:
    """Browser Agent выполняет действия в браузере"""
    logger.info("=" * 80)
    logger.info("🌐 BROWSER AGENT: Работа с браузером")
    logger.info("=" * 80)
    
    # Создаем словарь инструментов для быстрого поиска
    tools_by_name = {tool.name: tool for tool in tools}
    
    # Инициализация Chroma если включен
    chroma_tools = {}
    if state.get("chroma_enabled", False):
        logger.info("🔧 Инициализация Chroma инструментов...")
        chroma_tools = get_chroma_tools(tools)
        
        # Проверяем и создаем коллекции при первом запуске
        if not state.get("chroma_collections_ready", False):
            logger.info("📦 Проверка коллекций Chroma...")
            collections_ready = await ensure_collections_exist(chroma_tools)
            if collections_ready:
                state["chroma_collections_ready"] = True
                logger.info("✅ Коллекции Chroma готовы")
            else:
                logger.warning("⚠️ Не удалось инициализировать коллекции Chroma")
    
    # Проверяем авторизацию если браузер активен
    if state["browser_session_active"] and state["browser_status"] != "logged_in":
        logger.info("🔍 Проверка статуса авторизации...")
        is_logged_in = await _check_if_logged_in(tools_by_name)
        
        if is_logged_in:
            logger.info("✅ Пользователь уже авторизован!")
            state["browser_status"] = "logged_in"
            # Переходим к следующему шагу
            if not state["vacancies"]:
                logger.info("➡️ Переход к поиску вакансий")
        else:
            logger.info("❌ Пользователь не авторизован, требуется логин")
    
    # Определяем инструкции на основе текущего статуса
    if not state["browser_session_active"]:
        instructions = """1. Запусти браузер
2. Перейди на https://hh.ru
3. Проверь, есть ли на странице кнопка 'Войти' или элементы профиля пользователя
4. Если есть элементы профиля (имя пользователя, аватар) - пользователь уже авторизован
5. Если есть кнопка 'Войти' - выполни логин с credentials"""
        expected_status = "logged_in"
    elif state["browser_status"] == "logged_in" and not state["vacancies"]:
        if state.get("use_recommended", False):
            instructions = """1. Оставайся на главной странице HH (https://hh.ru или текущая страница)

2. Найди вкладку/кнопку "Для вас" (должна быть активна/выделена черным)
   Это блок с рекомендованными вакансиями специально для пользователя

3. Собери список вакансий из блока "Для вас" (первые 5-10 вакансий):
   Для каждой вакансии собери:
   - title (название вакансии, например "Python-разработчик AI")
   - company (название компании, например "Альфа-Банк. ИТ-специалисты")
   - url (ссылка на вакансию - кликабельный элемент)
   - salary (зарплата если указана, например "от 16 лет")
   - location (локация, например "Москва • Технопарк")
   - experience (опыт, например "Опыт 3-6 лет")
   - employment (тип занятости, например "Можно удалённо")
   - description (краткое описание из карточки если видно)

4. Верни список в формате JSON

ВАЖНО: 
- Используем ТОЛЬКО вакансии из блока "Для вас" (рекомендованные)
- НЕ переходи в раздел поиска
- НЕ используй вкладки "Подработка", "Вахта" и т.д.
- Ищи именно активную вкладку "Для вас" (выделена черным цветом)"""
        else:
            instructions = """1. Перейди в раздел поиска вакансий (https://hh.ru/search/vacancy)
2. Найди вакансии по критериям из плана
3. Собери список вакансий:
   - title (название)
   - company (компания)
   - url (ссылка)
   - description (краткое описание)
   - requirements (требования)
4. Верни список в формате JSON"""
        expected_status = "vacancies_found"
    elif state["cover_letter"]:
        resume_data = state.get("resume_data", {})
        full_name = resume_data.get("full_name", "")
        phone = resume_data.get("phone", "")
        email = resume_data.get("email", "")
        
        instructions = f"""1. Открой вакансию: {state['current_vacancy']['url']}
   ВАЖНО: Вакансия откроется в НОВОЙ ВКЛАДКЕ - переключись на неё!
   
2. Проверь наличие кнопки 'Откликнуться' или 'Respond' на странице:
   - Если кнопки НЕТ (есть текст "Отклик отправлен" или "Already applied") → 
     ПРОПУСТИ эту вакансию, верни статус 'already_applied'
   - Если кнопка ЕСТЬ → продолжай
   
3. Кликни на кнопку 'Откликнуться'

4. После открытия формы отклика проверь и заполни следующие поля (если они пустые или требуют заполнения):
   - Имя/ФИО: {full_name}
   - Телефон: {phone}
   - Email: {email}
   ВАЖНО: Обычно эти поля уже заполнены из профиля, но проверь их корректность!

5. Найди поле для сопроводительного письма (textarea, input)

6. Вставь письмо: {state['cover_letter'][:100]}...

7. Нажми кнопку отправки отклика ('Отправить', 'Send')

8. Закрой вкладку с вакансией и вернись на главную вкладку"""
        expected_status = "application_sent"
    else:
        instructions = "Определи, что нужно сделать на основе плана и текущего статуса"
        expected_status = "idle"
    
    current_plan_step = state["plan_steps"][state["current_step"]] if state["current_step"] < len(state["plan_steps"]) else "Выполнить текущую задачу"
    
    prompt = BROWSER_AGENT_PROMPT.format(
        current_plan_step=current_plan_step,
        hh_login=state["hh_login"],
        hh_password=state["hh_password"],
        browser_active=state["browser_session_active"],
        browser_status=state["browser_status"],
        browser_instructions=instructions
    )
    
    # ReAct цикл: модель → инструменты → модель → результат
    # Обрезаем историю сообщений для экономии токенов
    truncated_history = _truncate_messages(state["messages"])
    messages = truncated_history + [SystemMessage(content=prompt)]
    max_iterations = 50
    
    for iteration in range(max_iterations):
        logger.info(f"🔄 Browser Agent итерация {iteration + 1}/{max_iterations}")
        
        # Получаем ответ от модели с инструментами
        model_with_tools = model.bind_tools(tools)
        
        # Логируем количество инструментов и сообщений
        logger.debug(f"📊 Инструментов: {len(tools)}, Сообщений: {len(messages)}")
        
        # Дополнительная проверка: первое сообщение не должно быть ToolMessage
        non_system_messages = [msg for msg in messages if not isinstance(msg, SystemMessage)]
        if non_system_messages and isinstance(non_system_messages[0], ToolMessage):
            logger.error("❌ Обнаружен ToolMessage без предшествующего AIMessage! Исправляем...")
            # Удаляем все ToolMessage с начала, пока не найдем AIMessage
            while non_system_messages and isinstance(non_system_messages[0], ToolMessage):
                removed = non_system_messages.pop(0)
                logger.warning(f"   ⚠️ Удален ToolMessage: {removed.tool_call_id}")
            # Обновляем messages: системные + исправленные остальные
            system_msgs = [msg for msg in messages if isinstance(msg, SystemMessage)]
            messages = system_msgs + non_system_messages
        
        try:
            response = await model_with_tools.ainvoke(messages)
        except Exception as e:
            logger.error(f"❌ Ошибка при вызове модели: {e}")
            logger.error(f"   Последнее сообщение: {messages[-1] if messages else 'Нет сообщений'}")
            raise
        messages.append(response)
        
        # Если модель не вызывает инструменты, значит задача выполнена
        if not response.tool_calls:
            logger.info("✅ Browser Agent завершил работу (нет вызовов инструментов)")
            break
        
        # Выполняем все вызовы инструментов
        logger.info(f"🔧 Выполнение {len(response.tool_calls)} инструмент(ов):")
        tool_messages = []
        
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            tool_id = tool_call["id"]
            
            logger.info(f"  📌 {tool_name}({tool_args})")
            
            # Находим и выполняем инструмент
            if tool_name in tools_by_name:
                try:
                    tool = tools_by_name[tool_name]
                    # MCP инструменты асинхронные
                    tool_result = await tool.ainvoke(tool_args)
                    
                    # Обрезаем большие результаты для экономии токенов
                    truncated_result = _truncate_tool_result(str(tool_result), tool_name)
                    logger.info(f"     ✅ Результат: {truncated_result[:200]}")
                    
                    # Создаем сообщение с результатом
                    tool_messages.append(
                        ToolMessage(
                            content=truncated_result,
                            tool_call_id=tool_id,
                            name=tool_name
                        )
                    )
                except Exception as e:
                    logger.error(f"     ❌ Ошибка выполнения {tool_name}: {e}")
                    tool_messages.append(
                        ToolMessage(
                            content=f"Ошибка: {str(e)}",
                            tool_call_id=tool_id,
                            name=tool_name
                        )
                    )
            else:
                logger.warning(f"     ⚠️ Инструмент {tool_name} не найден")
                tool_messages.append(
                    ToolMessage(
                        content=f"Инструмент {tool_name} недоступен",
                        tool_call_id=tool_id,
                        name=tool_name
                    )
                )
        
        # Добавляем результаты инструментов в историю
        messages.extend(tool_messages)
        
        # Обрезаем историю сообщений после каждой итерации для экономии токенов
        # Оставляем место для следующей итерации (системное сообщение + ответ модели + результаты инструментов)
        messages = _truncate_messages(messages, max_messages=MAX_MESSAGES_HISTORY)
    
    # Обновляем состояние с ограничением истории
    # Обрезаем финальную историю перед сохранением
    state["messages"] = _truncate_messages(messages, max_messages=MAX_MESSAGES_HISTORY)
    
    # ============================================================================
    # КОМБИНИРОВАННАЯ ЛОГИКА ОПРЕДЕЛЕНИЯ СТАТУСА
    # ============================================================================
    last_response = str(messages[-1].content) if messages else ""
    
    # 1. Проверка логина
    if "logged_in" in expected_status or "успешно вошли" in last_response.lower() or "login" in last_response.lower():
        state["browser_session_active"] = True
        state["browser_status"] = "logged_in"
        logger.info("✅ Статус обновлен: logged_in")
        
    # 2. Проверка поиска вакансий
    elif "vacancies_found" in expected_status or "вакансии найдены" in last_response.lower():
        state["browser_status"] = "vacancies_found"
        if not state["vacancies"]:
            logger.warning("⚠️ Вакансии не найдены в результате, используем заглушку")
        logger.info("✅ Статус обновлен: vacancies_found")
        
    # 3. КОМБИНИРОВАННАЯ ПРОВЕРКА ОТПРАВКИ ОТКЛИКА
    elif expected_status == "application_sent":
        logger.info("🔍 Проверка отправки отклика (комбинированный подход)...")
        
        # Критерий A: Последовательность вызовов инструментов
        sequence_detected = _detect_application_sequence(messages)
        
        # Критерий B: Текстовые фразы в ответе LLM
        text_indicators = [
            "отклик отправлен",
            "успешно откликнулись",
            "application sent",
            "successfully applied",
            "отклик успешно"
        ]
        text_match = any(indicator in last_response.lower() for indicator in text_indicators)
        
        # Критерий C: Проверка через snapshot (опционально)
        snapshot_confirmed = False
        try:
            if "browser_snapshot" in tools_by_name:
                snapshot_tool = tools_by_name["browser_snapshot"]
                snapshot_result = await snapshot_tool.ainvoke({})
                snapshot_content = str(snapshot_result).lower()
                
                # Ищем подтверждающие элементы
                confirmation_texts = [
                    "отклик отправлен",
                    "ваш отклик отправлен",
                    "откликнулись на вакансию"
                ]
                snapshot_confirmed = any(text in snapshot_content for text in confirmation_texts)
                if snapshot_confirmed:
                    logger.info("   ✅ Snapshot подтверждает отправку отклика")
        except Exception as e:
            logger.debug(f"   ⚠️ Не удалось проверить snapshot: {e}")
        
        # РЕЗУЛЬТАТ: Если хотя бы один критерий выполнен
        application_successful = sequence_detected or text_match or snapshot_confirmed
        
        logger.info(f"   Критерии: sequence={sequence_detected}, text={text_match}, snapshot={snapshot_confirmed}")
        
        if application_successful:
            logger.info("✅ ОТКЛИК УСПЕШНО ОТПРАВЛЕН!")
            
            # Парсим детали вакансии если еще не сделано
            if state.get("current_vacancy"):
                logger.info("📋 Обновление информации о вакансии...")
                updated_vacancy = await _parse_vacancy_details(tools_by_name, state["current_vacancy"])
                state["current_vacancy"] = updated_vacancy
            
            # Обновляем статус и счетчик
            state["browser_status"] = "application_sent"
            state["applied_count"] += 1
            
            # Добавляем timestamp и метаданные
            from datetime import datetime
            current_vacancy = state.get("current_vacancy", {})
            current_vacancy["applied"] = True
            current_vacancy["applied_at"] = datetime.now().isoformat()
            current_vacancy["cover_letter"] = state.get("cover_letter", "")
            current_vacancy["session_id"] = state.get("session_id", "")
            
            # Добавляем URL в список уже откликнутых
            vacancy_url = current_vacancy.get("url", "")
            if vacancy_url and vacancy_url not in state["already_applied_urls"]:
                state["already_applied_urls"].add(vacancy_url)
                logger.info(f"   📌 URL добавлен в список откликнутых: {vacancy_url[:50]}...")
            
            # Добавляем в processed_vacancies
            if "processed_vacancies" not in state:
                state["processed_vacancies"] = []
            state["processed_vacancies"].append(current_vacancy.copy())
            logger.info(f"   💾 Вакансия добавлена в processed_vacancies (всего: {len(state['processed_vacancies'])})")
            
            # Сохраняем вакансию в Chroma если включен
            if state.get("chroma_enabled") and chroma_tools and current_vacancy:
                logger.info("💾 Сохранение вакансии в Chroma...")
                saved = await store_vacancy(chroma_tools, current_vacancy, state["session_id"])
                if saved:
                    state["vacancies_indexed"] = state.get("vacancies_indexed", 0) + 1
                    logger.info(f"✅ Вакансия сохранена в Chroma (всего: {state['vacancies_indexed']})")
            
            # Очищаем текущую вакансию и переходим к следующей
            state["current_vacancy_index"] += 1
            state["current_vacancy"] = None
            state["cover_letter"] = ""
            
            logger.info("=" * 80)
            logger.info(f"✅ Отклик #{state['applied_count']}/{state['max_applications']} успешно отправлен!")
            logger.info(f"   Вакансия: {current_vacancy.get('title', 'N/A')}")
            logger.info(f"   Компания: {current_vacancy.get('company', 'N/A')}")
            logger.info(f"   URL: {vacancy_url[:60]}...")
            logger.info("=" * 80)
        else:
            logger.warning("⚠️ Не удалось подтвердить отправку отклика")
    
    # 4. Обработка случая когда отклик уже был отправлен ранее
    elif "already_applied" in last_response.lower():
        logger.warning(f"⚠️ На вакансию '{state.get('current_vacancy', {}).get('title', 'Unknown')}' уже был отправлен отклик")
        logger.info("➡️ Пропускаем эту вакансию и переходим к следующей")
        
        # Добавляем URL в список уже откликнутых
        if state.get("current_vacancy"):
            vacancy_url = state['current_vacancy'].get('url', '')
            if vacancy_url and vacancy_url not in state["already_applied_urls"]:
                state["already_applied_urls"].add(vacancy_url)
        
        # Сохраняем информацию о дубликате в Chroma если включен
        if state.get("chroma_enabled") and chroma_tools and state.get("current_vacancy"):
            vacancy_data = state["current_vacancy"].copy()
            vacancy_data["applied"] = True
            vacancy_data["is_duplicate"] = True
            
            logger.info("💾 Сохранение информации о дубликате в Chroma...")
            await store_vacancy(chroma_tools, vacancy_data, state["session_id"])
        
        # Переходим к следующей вакансии без увеличения счетчика откликов
        state["current_vacancy_index"] += 1
        state["current_vacancy"] = None
        state["cover_letter"] = ""
        state["browser_status"] = "idle"
    
    return state

