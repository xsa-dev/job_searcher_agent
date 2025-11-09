"""
Утилиты для работы с Chroma векторным хранилищем через MCP инструменты
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


# Имена коллекций в Chroma
COLLECTION_VACANCIES = "job_vacancies"
COLLECTION_COVER_LETTERS = "cover_letters"
COLLECTION_RESUME = "resume_data"


def _normalize_metadata(value: Any) -> str | int | float | bool | None:
    """
    Нормализует значение метаданных для Chroma.
    
    Chroma принимает только простые типы: str, int, float, bool, None.
    Преобразует списки, словари и другие сложные типы в строки.
    
    Args:
        value: Значение для нормализации
        
    Returns:
        Нормализованное значение (str, int, float, bool, или None)
    """
    if value is None:
        return None
    
    if isinstance(value, (str, int, float, bool)):
        return value
    
    if isinstance(value, list):
        # Преобразуем список в строку через запятую
        return ", ".join(str(item) for item in value)
    
    if isinstance(value, dict):
        # Преобразуем словарь в JSON-подобную строку
        import json
        try:
            return json.dumps(value, ensure_ascii=False)
        except Exception:
            return str(value)
    
    # Для всех остальных типов - просто в строку
    return str(value)


def get_chroma_tools(all_tools: list) -> dict:
    """
    Извлекает Chroma инструменты из общего списка
    
    Args:
        all_tools: Список всех MCP инструментов
        
    Returns:
        Словарь с Chroma инструментами по именам
    """
    chroma_tool_names = [
        "create_collection",
        "list_collections",
        "add_documents",
        "query_documents",
        "delete_collection",
        "get_collection",
    ]
    
    chroma_tools = {}
    for tool in all_tools:
        if hasattr(tool, 'name') and tool.name in chroma_tool_names:
            chroma_tools[tool.name] = tool
    
    logger.info(f"🔍 Найдено {len(chroma_tools)} Chroma инструментов")
    return chroma_tools


async def ensure_collections_exist(chroma_tools: dict) -> bool:
    """
    Проверяет и создает необходимые коллекции в Chroma
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        
    Returns:
        True если коллекции созданы/существуют, False при ошибке
    """
    try:
        # Получаем список существующих коллекций
        list_tool = chroma_tools.get("list_collections")
        if not list_tool:
            logger.warning("⚠️ Инструмент list_collections не найден")
            return False
        
        existing_collections = await list_tool.ainvoke({})
        existing_names = [c.get("name") for c in existing_collections] if isinstance(existing_collections, list) else []
        
        logger.info(f"📋 Существующие коллекции: {existing_names}")
        
        # Создаем недостающие коллекции
        create_tool = chroma_tools.get("create_collection")
        if not create_tool:
            logger.warning("⚠️ Инструмент create_collection не найден")
            return False
        
        collections_to_create = [
            (COLLECTION_VACANCIES, "Коллекция вакансий с семантическим поиском"),
            (COLLECTION_COVER_LETTERS, "Коллекция сопроводительных писем"),
            (COLLECTION_RESUME, "Коллекция данных резюме и навыков"),
        ]
        
        for collection_name, description in collections_to_create:
            if collection_name not in existing_names:
                logger.info(f"🏗️ Создание коллекции: {collection_name}")
                try:
                    await create_tool.ainvoke({
                        "name": collection_name,
                        "metadata": {"description": description}
                    })
                    logger.info(f"✅ Коллекция {collection_name} создана")
                except Exception as e:
                    logger.error(f"❌ Ошибка создания коллекции {collection_name}: {e}")
            else:
                logger.info(f"✓ Коллекция {collection_name} уже существует")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке коллекций: {e}")
        return False


async def store_vacancy(
    chroma_tools: dict,
    vacancy: Dict[str, Any],
    session_id: str
) -> bool:
    """
    Сохраняет вакансию в Chroma для семантического поиска
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        vacancy: Данные вакансии
        session_id: ID текущей сессии
        
    Returns:
        True если успешно, False при ошибке
    """
    try:
        add_tool = chroma_tools.get("add_documents")
        if not add_tool:
            logger.warning("⚠️ Инструмент add_documents не найден")
            return False
        
        # Формируем текст для эмбеддинга
        vacancy_text = f"""
        Вакансия: {vacancy.get('title', '')}
        Компания: {vacancy.get('company', '')}
        Описание: {vacancy.get('description', '')}
        Требования: {vacancy.get('requirements', '')}
        Зарплата: {vacancy.get('salary', '')}
        Локация: {vacancy.get('location', '')}
        """
        
        # Метаданные (нормализуем все значения для Chroma)
        raw_metadata = {
            "url": vacancy.get("url", ""),
            "title": vacancy.get("title", ""),
            "company": vacancy.get("company", ""),
            "score": vacancy.get("score", 0.0),
            "applied": vacancy.get("applied", False),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
        }
        
        # Добавляем дополнительные поля если они есть (нормализуем)
        optional_fields = ["tags", "location", "salary", "description", "requirements"]
        for field in optional_fields:
            if field in vacancy and vacancy[field]:
                raw_metadata[field] = vacancy[field]
        
        # Нормализуем все значения метаданных
        metadata = {key: _normalize_metadata(value) for key, value in raw_metadata.items()}
        
        # Уникальный ID вакансии
        vacancy_id = vacancy.get("url", "").split("/")[-1] if vacancy.get("url") else f"vacancy_{hash(vacancy_text)}"
        
        await add_tool.ainvoke({
            "collection_name": COLLECTION_VACANCIES,
            "documents": [vacancy_text],
            "ids": [vacancy_id],
            "metadatas": [metadata],
        })
        
        logger.info(f"💾 Вакансия сохранена в Chroma: {vacancy.get('title', 'Unknown')}")
        return True
    
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения вакансии в Chroma: {e}")
        return False


async def search_similar_vacancies(
    chroma_tools: dict,
    query_text: str,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Поиск похожих вакансий в Chroma по семантическому сходству
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        query_text: Текст запроса для поиска
        n_results: Количество результатов
        
    Returns:
        Список похожих вакансий с метаданными
    """
    try:
        query_tool = chroma_tools.get("query_documents")
        if not query_tool:
            logger.warning("⚠️ Инструмент query_documents не найден")
            return []
        
        results = await query_tool.ainvoke({
            "collection_name": COLLECTION_VACANCIES,
            "query_texts": [query_text],
            "n_results": n_results,
        })
        
        logger.info(f"🔍 Найдено {len(results.get('metadatas', [[]])[0])} похожих вакансий")
        return results
    
    except Exception as e:
        logger.error(f"❌ Ошибка поиска похожих вакансий: {e}")
        return []


async def check_vacancy_duplicate(
    chroma_tools: dict,
    vacancy_url: str
) -> bool:
    """
    Проверяет, есть ли вакансия в Chroma (дубликат)
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        vacancy_url: URL вакансии для проверки
        
    Returns:
        True если дубликат найден, False если новая вакансия
    """
    try:
        # Ищем по URL в метаданных
        query_tool = chroma_tools.get("query_documents")
        if not query_tool:
            return False
        
        results = await query_tool.ainvoke({
            "collection_name": COLLECTION_VACANCIES,
            "query_texts": [vacancy_url],
            "n_results": 1,
            "where": {"url": vacancy_url},
        })
        
        # Если нашли результаты с таким URL - это дубликат
        if results and results.get("metadatas") and len(results["metadatas"][0]) > 0:
            logger.info(f"⚠️ Дубликат вакансии найден: {vacancy_url}")
            return True
        
        return False
    
    except Exception as e:
        logger.error(f"❌ Ошибка проверки дубликата: {e}")
        return False


async def store_cover_letter(
    chroma_tools: dict,
    vacancy: Dict[str, Any],
    cover_letter: str,
    session_id: str,
    was_successful: bool = False
) -> bool:
    """
    Сохраняет сопроводительное письмо в Chroma
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        vacancy: Данные вакансии
        cover_letter: Текст сопроводительного письма
        session_id: ID текущей сессии
        was_successful: Был ли отклик успешным
        
    Returns:
        True если успешно, False при ошибке
    """
    try:
        add_tool = chroma_tools.get("add_documents")
        if not add_tool:
            logger.warning("⚠️ Инструмент add_documents не найден")
            return False
        
        # Формируем документ для эмбеддинга
        document_text = f"""
        Вакансия: {vacancy.get('title', '')}
        Компания: {vacancy.get('company', '')}
        
        Сопроводительное письмо:
        {cover_letter}
        """
        
        # Метаданные (нормализуем все значения для Chroma)
        raw_metadata = {
            "vacancy_url": vacancy.get("url", ""),
            "vacancy_title": vacancy.get("title", ""),
            "company": vacancy.get("company", ""),
            "session_id": session_id,
            "successful": was_successful,
            "timestamp": datetime.now().isoformat(),
            "letter_length": len(cover_letter),
        }
        
        # Нормализуем все значения метаданных
        metadata = {key: _normalize_metadata(value) for key, value in raw_metadata.items()}
        
        # Уникальный ID письма
        letter_id = f"letter_{session_id}_{hash(cover_letter)}"
        
        await add_tool.ainvoke({
            "collection_name": COLLECTION_COVER_LETTERS,
            "documents": [document_text],
            "ids": [letter_id],
            "metadatas": [metadata],
        })
        
        logger.info(f"💾 Сопроводительное письмо сохранено в Chroma")
        return True
    
    except Exception as e:
        logger.error(f"❌ Ошибка сохранения письма в Chroma: {e}")
        return False


async def get_similar_cover_letters(
    chroma_tools: dict,
    vacancy: Dict[str, Any],
    n_results: int = 3,
    only_successful: bool = True
) -> List[Dict[str, Any]]:
    """
    Поиск похожих сопроводительных писем для вакансии
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        vacancy: Данные вакансии
        n_results: Количество результатов
        only_successful: Искать только успешные письма
        
    Returns:
        Список похожих писем с метаданными
    """
    try:
        query_tool = chroma_tools.get("query_documents")
        if not query_tool:
            logger.warning("⚠️ Инструмент query_documents не найден")
            return []
        
        # Формируем запрос
        query_text = f"Вакансия: {vacancy.get('title', '')} Компания: {vacancy.get('company', '')}"
        
        query_params = {
            "collection_name": COLLECTION_COVER_LETTERS,
            "query_texts": [query_text],
            "n_results": n_results,
        }
        
        # Фильтр только по успешным письмам
        if only_successful:
            query_params["where"] = {"successful": "True"}
        
        results = await query_tool.ainvoke(query_params)
        
        logger.info(f"🔍 Найдено {len(results.get('documents', [[]])[0])} похожих писем")
        return results
    
    except Exception as e:
        logger.error(f"❌ Ошибка поиска похожих писем: {e}")
        return []


async def store_resume_skills(
    chroma_tools: dict,
    resume_data: Dict[str, Any]
) -> bool:
    """
    Индексирует навыки и данные резюме в Chroma
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        resume_data: Данные резюме
        
    Returns:
        True если успешно, False при ошибке
    """
    try:
        add_tool = chroma_tools.get("add_documents")
        if not add_tool:
            logger.warning("⚠️ Инструмент add_documents не найден")
            return False
        
        # Формируем документ
        resume_text = f"""
        Должность: {resume_data.get('title', '')}
        Навыки: {', '.join(resume_data.get('tags', []))}
        Описание: {resume_data.get('summary', '')}
        """
        
        # Метаданные (нормализуем все значения для Chroma)
        raw_metadata = {
            "resume_id": resume_data.get("id", "default"),
            "title": resume_data.get("title", ""),
            "timestamp": datetime.now().isoformat(),
        }
        
        # Добавляем дополнительные поля если они есть
        optional_fields = ["tags", "full_name", "email", "phone"]
        for field in optional_fields:
            if field in resume_data and resume_data[field]:
                raw_metadata[field] = resume_data[field]
        
        # Нормализуем все значения метаданных
        metadata = {key: _normalize_metadata(value) for key, value in raw_metadata.items()}
        
        resume_id = f"resume_{resume_data.get('id', 'default')}"
        
        await add_tool.ainvoke({
            "collection_name": COLLECTION_RESUME,
            "documents": [resume_text],
            "ids": [resume_id],
            "metadatas": [metadata],
        })
        
        logger.info(f"💾 Данные резюме проиндексированы в Chroma")
        return True
    
    except Exception as e:
        logger.error(f"❌ Ошибка индексации резюме: {e}")
        return False


async def get_vacancy_history(
    chroma_tools: dict,
    vacancy_title: str,
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """
    Получает историю работы с похожими вакансиями
    
    Args:
        chroma_tools: Словарь Chroma инструментов
        vacancy_title: Название вакансии
        n_results: Количество результатов
        
    Returns:
        Список похожих вакансий из истории
    """
    try:
        query_tool = chroma_tools.get("query_documents")
        if not query_tool:
            logger.warning("⚠️ Инструмент query_documents не найден")
            return []
        
        results = await query_tool.ainvoke({
            "collection_name": COLLECTION_VACANCIES,
            "query_texts": [vacancy_title],
            "n_results": n_results,
            "where": {"applied": "True"},
        })
        
        logger.info(f"📊 Найдено {len(results.get('metadatas', [[]])[0])} вакансий в истории")
        return results
    
    except Exception as e:
        logger.error(f"❌ Ошибка получения истории вакансий: {e}")
        return []


def format_chroma_results(results: Dict[str, Any]) -> str:
    """
    Форматирует результаты из Chroma в читаемый текст
    
    Args:
        results: Результаты запроса из Chroma
        
    Returns:
        Форматированная строка с результатами
    """
    if not results or not results.get("documents"):
        return "Нет результатов"
    
    formatted = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0] if "distances" in results else [None] * len(documents)
    
    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        formatted.append(f"\n--- Результат {i+1} ---")
        if dist is not None:
            formatted.append(f"Расстояние: {dist:.4f}")
        formatted.append(f"Метаданные: {meta}")
        formatted.append(f"Документ:\n{doc[:500]}...")  # Первые 500 символов
    
    return "\n".join(formatted)


