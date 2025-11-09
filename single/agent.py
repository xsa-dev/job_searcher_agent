from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langchain.agents.middleware.types import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
import asyncio
import time
import logging
from typing import Any, Dict, List
from collections.abc import Callable, Awaitable

from hide_me import api_key
from prompt import template

# Удалена неиспользуемая память AgentMemory - история управляется агентом автоматически

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Включаем DEBUG для httpx чтобы видеть запросы
logging.getLogger("httpx").setLevel(logging.INFO)


class HistoryLimitMiddleware(AgentMiddleware):
    """Middleware для ограничения размера истории сообщений перед вызовом модели"""

    def __init__(self, max_messages: int = 20, keep_system: bool = True):
        """
        Args:
            max_messages: Максимальное количество сообщений для передачи в модель
            keep_system: Сохранять ли system prompt отдельно
        """
        self.max_messages = max_messages
        self.keep_system = keep_system

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """Ограничивает размер истории перед вызовом модели (асинхронная версия)"""
        messages = request.messages
        system_prompt = request.system_prompt

        # Подсчитываем общее количество сообщений
        total_messages = len(messages)
        if system_prompt:
            total_messages += 1

        # Если сообщений слишком много, обрезаем
        if total_messages > self.max_messages:
            # Оставляем system prompt и последние N сообщений
            messages_to_keep = self.max_messages - (1 if system_prompt else 0)

            # Берем последние сообщения
            trimmed_messages = (
                messages[-messages_to_keep:]
                if len(messages) > messages_to_keep
                else messages
            )

            logger.warning(
                f"⚠️  История обрезана: {len(messages)} -> {len(trimmed_messages)} сообщений "
                f"(лимит: {self.max_messages})"
            )

            # Создаем новый запрос с обрезанными сообщениями
            request = request.override(messages=trimmed_messages)

        # Вызываем оригинальный handler
        return await handler(request)


class AgentCallbackHandler(BaseCallbackHandler):
    """Callback для логирования действий агента"""

    def __init__(self):
        self.step_count = 0

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Вызывается когда LLM начинает работу"""
        self.step_count += 1
        logger.info("=" * 80)
        logger.info(f"🤖 LLM ЗАПУСК (шаг {self.step_count})")
        logger.info("=" * 80)
        for i, prompt in enumerate(prompts):
            logger.info(f"Промпт {i + 1}:")
            logger.info(f"{prompt[:500]}..." if len(prompt) > 500 else prompt)

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Вызывается когда LLM завершает работу"""
        logger.info("-" * 80)
        logger.info(f"✅ LLM ЗАВЕРШИЛ (шаг {self.step_count})")
        if response.generations:
            for gen_list in response.generations:
                for gen in gen_list:
                    if hasattr(gen, "text"):
                        text = (
                            gen.text[:500] + "..." if len(gen.text) > 500 else gen.text
                        )
                        logger.info(f"Ответ модели: {text}")
                    if hasattr(gen, "message"):
                        content = (
                            str(gen.message.content)[:500] + "..."
                            if len(str(gen.message.content)) > 500
                            else str(gen.message.content)
                        )
                        logger.info(f"Ответ модели: {content}")
        logger.info("=" * 80)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> None:
        """Вызывается при ошибке LLM"""
        logger.error(f"❌ ОШИБКА LLM: {error}")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Вызывается когда инструмент начинает работу"""
        tool_name = serialized.get("name", "unknown")
        logger.info("🔧 ИНСТРУМЕНТ ЗАПУСК:")
        logger.info(f"  Название: {tool_name}")
        logger.info(f"  Входные данные: {input_str}")

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        """Вызывается когда инструмент завершает работу"""
        if hasattr(output, "content"):
            output_str = str(output.content)
        else:
            output_str = str(output)
        output_preview = (
            output_str[:500] + "..." if len(output_str) > 500 else output_str
        )
        logger.info("✅ ИНСТРУМЕНТ ЗАВЕРШИЛ:")
        logger.info(f"  Результат: {output_preview}")

    def on_tool_error(self, error: Exception, **kwargs: Any) -> None:
        """Вызывается при ошибке инструмента"""
        logger.error(f"❌ ОШИБКА ИНСТРУМЕНТА: {error}")

    def on_agent_finish(self, finish, **kwargs: Any) -> None:
        """Вызывается когда агент завершает работу"""
        logger.info("🏁 АГЕНТ ЗАВЕРШИЛ РАБОТУ")
        logger.info(f"  Результат: {finish.return_values}")

    def on_chain_error(self, error: Exception, **kwargs: Any) -> None:
        """Вызывается при ошибке цепочки"""
        logger.error(f"❌ ОШИБКА ЦЕПОЧКИ: {error}")


logger.info("Инициализация MCP клиента...")
client = MultiServerMCPClient(
    {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
            "transport": "stdio",
        }
    }
)

logger.info("MCP клиент инициализирован")

logger.info("Инициализация модели...")
foundation_model = ChatOpenAI(
    model="MiniMaxAI/MiniMax-M2",
    base_url="https://foundation-models.api.cloud.ru/v1",
    api_key=api_key,
    temperature=0.5,
    max_tokens=5000,
    timeout=180,
    max_retries=2,
    top_p=0.95,
    model_kwargs={
        "presence_penalty": 0,
    }
)
logger.info("Модель инициализирована (timeout=180s, max_retries=2, temperature=0.3)")
logger.info("Получение инструментов от MCP клиента...")


# Создаем инструмент для ожидания
class WaitInput(BaseModel):
    """Входные параметры для инструмента wait"""

    seconds: float = Field(
        default=10.0,
        description="Количество секунд для ожидания. По умолчанию 3 секунды. Используйте это после запуска браузера, чтобы дать ему время инициализироваться.",
    )


def wait_tool(seconds: float = 3.0) -> str:
    """Ожидает указанное количество секунд. Используйте этот инструмент после start_browser, чтобы дать браузеру время полностью запуститься."""
    logger.info(f"⏳ Ожидание {seconds} секунд...")
    time.sleep(seconds)
    logger.info(f"✅ Ожидание завершено ({seconds} секунд)")
    return f"Ожидание завершено. Прошло {seconds} секунд."


wait_tool_instance = StructuredTool.from_function(
    func=wait_tool,
    name="wait",
    description="Ожидает указанное количество секунд. КРИТИЧЕСКИ ВАЖНО: Используйте этот инструмент сразу после start_browser, чтобы дать браузеру время полностью запуститься и инициализироваться. Рекомендуется использовать wait(seconds=3) или wait(seconds=5) после запуска браузера.",
    args_schema=WaitInput,
)


async def main(user_query):
    logger.info("Создание callback handler...")
    callback_handler = AgentCallbackHandler()
    logger.info("Callback handler создан")
    
    try:
        async with client.session("playwright") as mcp_session:
            # Загружаем инструменты с использованием одной сессии
            mcp_tools = await load_mcp_tools(
                session=mcp_session,
                server_name="playwright",
            )

            # Добавляем инструмент ожидания к списку инструментов
            tools = list(mcp_tools) + [wait_tool_instance]
            logger.info("Добавлен инструмент 'wait' к списку инструментов")

            # Проверяем параметры инструментов, особенно timeout
            logger.info("=" * 80)
            logger.info("ПАРАМЕТРЫ ИНСТРУМЕНТОВ:")
            logger.info("=" * 80)
            for tool in tools:
                if hasattr(tool, "args_schema") and tool.args_schema:
                    schema = (
                        tool.args_schema.model_json_schema()
                        if hasattr(tool.args_schema, "model_json_schema")
                        else {}
                    )
                    properties = schema.get("properties", {})
                    has_timeout = "timeout" in properties
                    logger.info(f"Инструмент: {tool.name}")
                    logger.info(f"  - Есть параметр timeout: {has_timeout}")
                    if has_timeout:
                        timeout_info = properties["timeout"]
                        logger.info(f"  - timeout: {timeout_info}")
                    logger.info("")

            # Создаем middleware для ограничения истории (критически важно для предотвращения превышения лимита токенов)
            history_middleware = HistoryLimitMiddleware(
                max_messages=15
            )  # Ограничиваем до 15 сообщений

            agent = create_agent(
                system_prompt=template,
                model=foundation_model,
                tools=tools,
                middleware=[
                    history_middleware
                ],  # Добавляем middleware для ограничения истории
            )
            
            result = await agent.ainvoke(
                {"input": user_query}, config={"callbacks": [callback_handler]}
            )
            logger.info(f"Результат: {result}")

            # Не закрываем браузер автоматически - оставляем его открытым для проверки
            logger.info("⚠️  Браузер остается открытым. Закройте его вручную.")

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
                logger.error(f"❌ Ошибка при выполнении задачи: {exc}")
                raise exc


if __name__ == "__main__":
    asyncio.run(main(""))
