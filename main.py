"""
Точка входа для мультиагентной системы по откликам на вакансии HeadHunter
"""

import asyncio
import logging
from contextlib import AsyncExitStack

from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from graph_agent import create_graph, create_initial_state
from utils.storage import SessionStorage
from config_loader import (
    load_config,
    get_resume_data,
    get_hh_credentials,
    get_search_settings,
)
from hide_me import api_key

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска мультиагентной системы"""
    
    logger.info("=" * 80)
    logger.info("🚀 ЗАПУСК МУЛЬТИАГЕНТНОЙ СИСТЕМЫ")
    logger.info("=" * 80)
    
    # Инициализация хранилища сессий
    storage = SessionStorage(data_dir="data/sessions")
    
    # Загрузка истории предыдущих сессий
    logger.info("📂 Загрузка истории сессий...")
    previous_sessions = storage.load_recent_sessions(limit=5)  # Уменьшаем с 10 до 5
    already_applied_urls = storage.get_already_applied_urls(limit=30)  # Уменьшаем с 50 до 30
    
    # Статистика
    stats = storage.get_statistics()
    logger.info("📊 Статистика:")
    logger.info(f"  - Всего сессий: {stats['total_sessions']}")
    logger.info(f"  - Всего откликов: {stats['total_applications']}")
    logger.info(f"  - Средний score: {stats['average_score']:.2f}")
    
    # Инициализация MCP клиента для браузера и Chroma
    logger.info("🌐 Инициализация MCP клиентов (Playwright + Chroma)...")
    
    # # Chroma опционален - проверяем доступность
    chroma_enabled = True
    
    # Настраиваем клиенты
    client_config = {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
            "transport": "stdio",
        }
    }
    
    if chroma_enabled:
        client_config["chroma"] = {
            "command": "uvx",
            "args": [
                "chroma-mcp",
                "--client-type",
                "persistent",
                "--data-dir",
                "/Users/alxy/Desktop/1PROJ/PrometheusAi/job_searcher_agent/chroma_data"
            ],
            "transport": "stdio",
        }
    
    client = MultiServerMCPClient(client_config)
    
    # Инициализация модели
    logger.info("🤖 Инициализация Foundation Model (MiniMaxAI/MiniMax-M2)...")
    foundation_model = ChatOpenAI(
        model="MiniMaxAI/MiniMax-M2",
        base_url="https://foundation-models.api.cloud.ru/v1",
        api_key=api_key,
        temperature=0.5,
        # max_tokens=256000,
        timeout=180,
        max_retries=5,
        top_p=0.95,
        model_kwargs={
            "presence_penalty": 0,
        }
    )
    
    try:
        # Используем AsyncExitStack для управления несколькими сессиями
        async with AsyncExitStack() as stack:
            # Playwright обязателен
            playwright_session = await stack.enter_async_context(
                client.session("playwright")
            )
            
            # Загружаем MCP инструменты из Playwright
            logger.info("🔧 Загрузка Playwright MCP инструментов...")
            playwright_tools = await load_mcp_tools(
                session=playwright_session,
                server_name="playwright",
            )
            logger.info(f"✅ Загружено {len(playwright_tools)} Playwright инструментов")
            
            # Chroma опционален
            chroma_tools = []
            if chroma_enabled:
                try:
                    chroma_session = await stack.enter_async_context(
                        client.session("chroma")
                    )
                    logger.info("🔧 Загрузка Chroma MCP инструментов...")
                    chroma_tools = await load_mcp_tools(
                        session=chroma_session,
                        server_name="chroma",
                    )
                    logger.info(f"✅ Загружено {len(chroma_tools)} Chroma инструментов")
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось подключиться к Chroma: {e}")
                    logger.info("   Продолжаем работу без Chroma инструментов")
                    chroma_enabled = False
            else:
                logger.info("⏭️ Chroma пропущен (недоступен)")
            
            # Объединяем все инструменты
            mcp_tools = playwright_tools + chroma_tools
            
            # Исправляем схемы инструментов для совместимости с Foundation Model API
            for tool in mcp_tools:
                try:
                    schema = tool.get_input_schema()
                    if isinstance(schema, dict) and "required" in schema and not isinstance(schema["required"], list):
                        # Если required не список, делаем его пустым списком
                        schema["required"] = []
                        logger.debug(f"🔧 Исправлена схема инструмента {tool.name}")
                except Exception as e:
                    logger.debug(f"⚠️ Не удалось проверить схему {tool.name}: {e}")
            
            logger.info(f"✅ Всего загружено {len(mcp_tools)} инструментов")
            logger.info(f"📋 Список инструментов: {[t.name for t in mcp_tools][:15]}...")
            
            # Загружаем конфигурацию
            logger.info("📋 Загрузка конфигурации...")
            config = load_config()
            
            # Загружаем данные резюме из конфига
            resume_data = get_resume_data(config)
            logger.info(f"✅ Данные резюме загружены: {resume_data.get('full_name', 'N/A')}")
            
            # Загружаем credentials из конфига
            hh_login, hh_password = get_hh_credentials(config)
            if not hh_login or not hh_password:
                raise ValueError("Не указаны credentials для HeadHunter в config.json")
            logger.info(f"✅ Credentials загружены для: {hh_login}")
            
            # Загружаем настройки поиска
            search_settings = get_search_settings(config)
            max_applications = search_settings.get("max_applications", 5)
            vacancy_query = search_settings.get("vacancy_search_query", "Python Backend разработчик")
            city = search_settings.get("city", "Москва")
            
            # Формируем user_request на основе настроек
            user_request = f"Откликнуться на {max_applications} подходящих вакансий {vacancy_query} в {city}"
            
            # Создаем граф
            logger.info("🏗️ Создание графа мультиагентной системы...")
            try:
                graph = create_graph(mcp_tools, foundation_model)
                logger.info("✅ Граф создан успешно")
            except Exception as e:
                logger.error(f"❌ Ошибка при создании графа: {e}")
                raise
            
            # Создаем начальное состояние
            logger.info("📝 Создание начального состояния...")
            
            # Параметр use_recommended: True = использовать рекомендованные вакансии (быстрее)
            # False = детальный поиск по критериям (больше контроля)
            use_recommended = True  # Можно сделать параметром командной строки
            
            initial_state = create_initial_state(
                user_request=user_request,
                resume_data=resume_data,
                hh_login=hh_login,
                hh_password=hh_password,
                max_applications=max_applications,
                previous_sessions=previous_sessions,
                already_applied_urls=already_applied_urls,
                use_recommended=use_recommended,
                chroma_enabled=chroma_enabled
            )
            
            logger.info(f"🎯 Режим поиска: {'Рекомендованные вакансии (блок \"Для вас\")' if use_recommended else 'Детальный поиск по критериям'}")
            
            logger.info("=" * 80)
            logger.info("🎬 ЗАПУСК ГРАФА")
            logger.info("=" * 80)
            
            # Запускаем граф
            final_state = await graph.ainvoke(initial_state)
            
            logger.info("=" * 80)
            logger.info("✅ ГРАФ ЗАВЕРШЕН")
            logger.info("=" * 80)
            
            # Сохраняем результаты сессии
            logger.info("💾 Сохранение результатов сессии...")
            session_id = storage.save_session(final_state)
            
            # Выводим итоговую статистику
            logger.info("=" * 80)
            logger.info("📊 ИТОГОВАЯ СТАТИСТИКА СЕССИИ")
            logger.info("=" * 80)
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Откликов отправлено: {final_state['applied_count']}/{final_state['max_applications']}")
            logger.info(f"Вакансий найдено: {len(final_state['vacancies'])}")
            logger.info(f"Вакансий обработано: {final_state['current_vacancy_index']}")
            logger.info(f"Статус браузера: {final_state['browser_status']}")
            
            if final_state.get("error_message"):
                logger.error(f"❌ Ошибка: {final_state['error_message']}")
            
            logger.info("=" * 80)
            logger.info("🏁 РАБОТА ЗАВЕРШЕНА")
            logger.info("=" * 80)
            
    except* (RuntimeError, Exception) as eg:
        # Обработка ExceptionGroup от anyio/asyncio
        for exc in eg.exceptions:
            error_msg = str(exc)
            exc_type = type(exc).__name__
            
            # Игнорируем известные ошибки MCP серверов
            ignored_errors = [
                "cancel scope",
                "Maximum call stack",
                "Shutdown signal received",
                "Invalid JSON",
                "BrokenResourceError",
                "ValidationError"
            ]
            
            # Проверяем и по строке, и по типу исключения
            should_ignore = any(err in error_msg for err in ignored_errors) or \
                           any(err in exc_type for err in ignored_errors)
            
            if should_ignore:
                logger.warning(
                    f"⚠️  Ошибка при закрытии MCP сессии (игнорируется): {exc_type}: {error_msg[:100]}..."
                )
            else:
                logger.error(f"❌ Критическая ошибка при выполнении: {exc}")
                raise exc


if __name__ == "__main__":
    asyncio.run(main())
