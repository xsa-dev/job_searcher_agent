"""
Инструменты для мультиагентной системы
"""

import logging
import time

from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)


class WaitInput(BaseModel):
    """Входные параметры для инструмента wait"""
    seconds: float = Field(
        default=3.0,
        description="Количество секунд для ожидания"
    )


def wait_tool(seconds: float = 3.0) -> str:
    """Ожидает указанное количество секунд"""
    logger.info(f"⏳ Ожидание {seconds} секунд...")
    time.sleep(seconds)
    return f"Ожидание завершено ({seconds} секунд)"


wait_tool_instance = StructuredTool.from_function(
    func=wait_tool,
    name="wait",
    description="Ожидает указанное количество секунд. Используй после start_browser или других операций, требующих времени на инициализацию.",
    args_schema=WaitInput,
)

