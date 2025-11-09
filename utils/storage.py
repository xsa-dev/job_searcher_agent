"""
Модуль для сохранения и загрузки истории сессий работы мультиагентной системы
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SessionStorage:
    """Класс для работы с хранением сессий в JSON файлах"""
    
    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir.parent / "history.json"
        logger.info(f"📁 SessionStorage инициализирован: {self.data_dir}")
    
    def save_session(self, state: dict) -> str:
        """
        Сохраняет сессию в JSON файл
        
        Args:
            state: Состояние AgentState (как dict)
            
        Returns:
            session_id: ID сохраненной сессии
        """
        session_id = state.get("session_id", str(uuid.uuid4()))
        timestamp = datetime.now()
        
        # Формируем данные для сохранения
        session_data = {
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "user_request": state.get("user_request", ""),
            "plan": state.get("plan", ""),
            "plan_steps": state.get("plan_steps", []),
            "resume_used": state.get("resume_data", {}),
            "vacancies_processed": self._format_vacancies(state),
            "statistics": {
                "total_vacancies_found": len(state.get("vacancies", [])),
                "total_analyzed": len(state.get("vacancies", [])),
                "total_applied": state.get("applied_count", 0),
                "total_rejected": state.get("rejected_count", 0),
                "average_score": self._calculate_average_score(state.get("vacancies", [])),
                "execution_time": int(state.get("start_time", 0) and (datetime.now().timestamp() - state.get("start_time", 0)))
            }
        }
        
        # Сохраняем в файл
        filename = f"session_{session_id}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.data_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 Сессия сохранена: {filename}")
        
        # Обновляем общую историю
        self._update_history(session_id, timestamp)
        
        return session_id
    
    def load_recent_sessions(self, limit: int = 10) -> list[dict]:
        """
        Загружает последние N сессий
        
        Args:
            limit: Максимальное количество сессий для загрузки
            
        Returns:
            Список сессий, отсортированных по времени (новые первые)
        """
        session_files = sorted(
            self.data_dir.glob("session_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        sessions = []
        for session_file in session_files[:limit]:
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    session_data = json.load(f)
                    # ОГРАНИЧЕНИЕ: Сохраняем только ключевые данные для экономии токенов
                    limited_session = {
                        "session_id": session_data.get("session_id"),
                        "timestamp": session_data.get("timestamp"),
                        "statistics": session_data.get("statistics", {}),
                        "vacancies_processed": session_data.get("vacancies_processed", [])[:3]  # Только первые 3 вакансии
                    }
                    sessions.append(limited_session)
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки сессии {session_file}: {e}")
        
        logger.info(f"📂 Загружено {len(sessions)} сессий из истории (с ограничением данных)")
        return sessions
    
    def check_vacancy_applied(self, vacancy_url: str, sessions: Optional[list[dict]] = None) -> bool:
        """
        Проверяет, откликались ли уже на вакансию по URL
        
        Args:
            vacancy_url: URL вакансии
            sessions: Список сессий (если None, загружаются автоматически)
            
        Returns:
            True если уже откликались, False иначе
        """
        if sessions is None:
            sessions = self.load_recent_sessions(limit=50)
        
        for session in sessions:
            vacancies = session.get("vacancies_processed", [])
            for vacancy in vacancies:
                if vacancy.get("url") == vacancy_url and vacancy.get("applied"):
                    logger.info(f"⚠️ Уже откликались на вакансию: {vacancy_url}")
                    return True
        
        return False
    
    def get_already_applied_urls(self, limit: int = 50) -> set[str]:
        """
        Получает множество URL вакансий, на которые уже откликались
        
        Args:
            limit: Количество последних сессий для проверки
            
        Returns:
            Множество URL вакансий
        """
        sessions = self.load_recent_sessions(limit=limit)
        applied_urls = set()
        
        for session in sessions:
            vacancies = session.get("vacancies_processed", [])
            for vacancy in vacancies:
                if vacancy.get("applied") and vacancy.get("url"):
                    applied_urls.add(vacancy["url"])
        
        logger.info(f"📊 Найдено {len(applied_urls)} вакансий с откликами в истории")
        return applied_urls
    
    def get_statistics(self) -> dict:
        """
        Получает общую статистику по всем сессиям
        
        Returns:
            Словарь со статистикой
        """
        sessions = self.load_recent_sessions(limit=100)
        
        if not sessions:
            return {
                "total_sessions": 0,
                "total_applications": 0,
                "total_vacancies_found": 0,
                "average_score": 0.0,
                "last_session": None
            }
        
        stats = {
            "total_sessions": len(sessions),
            "total_applications": sum(s.get("statistics", {}).get("total_applied", 0) for s in sessions),
            "total_vacancies_found": sum(s.get("statistics", {}).get("total_vacancies_found", 0) for s in sessions),
            "average_score": sum(s.get("statistics", {}).get("average_score", 0.0) for s in sessions) / len(sessions),
            "last_session": sessions[0].get("timestamp") if sessions else None
        }
        
        return stats
    
    def _format_vacancies(self, state: dict) -> list[dict]:
        """Форматирует вакансии для сохранения"""
        # Приоритет: используем processed_vacancies если есть, иначе vacancies
        source_vacancies = state.get("processed_vacancies", state.get("vacancies", []))
        vacancies = []
        
        for vacancy in source_vacancies:
            vacancy_data = {
                "url": vacancy.get("url", ""),
                "title": vacancy.get("title", ""),
                "company": vacancy.get("company", ""),
                "salary": vacancy.get("salary", ""),
                "location": vacancy.get("location", ""),
                "score": vacancy.get("score", 0.0),
                "cover_letter": vacancy.get("cover_letter", ""),
                "applied": vacancy.get("applied", False),
                "applied_at": vacancy.get("applied_at"),
                "rejection_reason": vacancy.get("rejection_reason"),
                "session_id": vacancy.get("session_id", "")
            }
            vacancies.append(vacancy_data)
        
        return vacancies
    
    def _calculate_average_score(self, vacancies: list[dict]) -> float:
        """Вычисляет средний score вакансий"""
        if not vacancies:
            return 0.0
        
        scores = [v.get("score", 0.0) for v in vacancies if v.get("score")]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _update_history(self, session_id: str, timestamp: datetime):
        """Обновляет файл общей истории"""
        if self.history_file.exists():
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        else:
            history = {
                "total_sessions": 0,
                "last_session": None,
                "sessions": []
            }
        
        history["total_sessions"] += 1
        history["last_session"] = timestamp.isoformat()
        history["sessions"].append(session_id)
        
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

