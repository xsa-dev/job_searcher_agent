"""
Загрузка конфигурации для мультиагентной системы
"""

import json
from pathlib import Path
from typing import Optional


def load_config(config_path: str = "config.json") -> dict:
    """
    Загружает конфигурацию из JSON файла
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Словарь с конфигурацией
        
    Raises:
        FileNotFoundError: Если файл не найден
        json.JSONDecodeError: Если файл содержит невалидный JSON
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(
            f"Файл конфигурации не найден: {config_path}\n"
            f"Создайте config.json на основе config.example.json"
        )
    
    with open(config_file, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return config


def get_resume_data(config: Optional[dict] = None) -> dict:
    """
    Извлекает данные резюме из конфига
    
    Args:
        config: Словарь конфигурации (если None, загружается автоматически)
        
    Returns:
        Данные резюме со всеми полями (full_name, phone, email, work_history, education и т.д.)
        
    Raises:
        ValueError: Если отсутствуют обязательные поля
    """
    if config is None:
        config = load_config()
    
    resume_data = config.get("resume", {})
    
    # Валидация обязательных полей
    required_fields = ["id", "title", "full_name", "email", "phone"]
    missing_fields = [field for field in required_fields if not resume_data.get(field)]
    
    if missing_fields:
        raise ValueError(
            f"Отсутствуют обязательные поля резюме: {', '.join(missing_fields)}\n"
            f"Проверьте файл config.json"
        )
    
    return resume_data


def get_hh_credentials(config: Optional[dict] = None) -> tuple[str, str]:
    """
    Извлекает credentials для HeadHunter
    
    Args:
        config: Словарь конфигурации (если None, загружается автоматически)
        
    Returns:
        Кортеж (login, password)
    """
    if config is None:
        config = load_config()
    
    credentials = config.get("hh_credentials", {})
    return credentials.get("login", ""), credentials.get("password", "")


def get_search_settings(config: Optional[dict] = None) -> dict:
    """
    Извлекает настройки поиска вакансий
    
    Args:
        config: Словарь конфигурации (если None, загружается автоматически)
        
    Returns:
        Настройки поиска
    """
    if config is None:
        config = load_config()
    
    return config.get("search_settings", {})


def get_llm_settings(config: Optional[dict] = None) -> dict:
    """
    Извлекает настройки LLM
    
    Args:
        config: Словарь конфигурации (если None, загружается автоматически)
        
    Returns:
        Настройки LLM
    """
    if config is None:
        config = load_config()
    
    return config.get("llm_settings", {})


def get_history_settings(config: Optional[dict] = None) -> dict:
    """
    Извлекает настройки истории
    
    Args:
        config: Словарь конфигурации (если None, загружается автоматически)
        
    Returns:
        Настройки истории
    """
    if config is None:
        config = load_config()
    
    return config.get("history_settings", {})

