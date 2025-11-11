# Архитектурный план: Поддержка множественных источников вакансий

## 1. Обзор

### 1.1 Цель
Расширение мультиагентной системы для работы с несколькими источниками вакансий (HeadHunter, SuperJob и другими), обеспечивая унифицированный интерфейс и возможность параллельного поиска.

### 1.2 Текущее состояние
- **Источники**: Только HeadHunter (hh.ru)
- **Метод работы**: Browser automation через Playwright MCP
- **Жесткая привязка**: Код содержит прямые ссылки на hh.ru, специфичные селекторы и логику HH
- **Структура вакансий**: Унифицированная структура в `AgentState.vacancies`

### 1.3 Целевое состояние
- **Множественные источники**: HeadHunter, SuperJob, и возможность добавления других
- **Унифицированный интерфейс**: Абстракция для работы с любым источником
- **Гибкость**: Поддержка как browser automation, так и API-интеграций
- **Параллельный поиск**: Возможность поиска на нескольких источниках одновременно

## 2. Архитектура источников

### 2.1 Абстракция источника вакансий

**Базовый интерфейс `VacancySource`:**

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class VacancySourceConfig:
    """Конфигурация источника вакансий"""
    name: str  # "hh", "superjob", "habr_career", etc.
    enabled: bool
    credentials: Dict[str, str]  # Логин, пароль, API ключи
    search_params: Dict[str, Any]  # Параметры поиска
    method: str  # "browser" или "api"

@dataclass
class UnifiedVacancy:
    """Унифицированная структура вакансии"""
    # Обязательные поля
    source: str  # "hh", "superjob", etc.
    source_id: str  # ID вакансии в источнике
    url: str  # URL вакансии
    title: str  # Название вакансии
    company: str  # Название компании
    
    # Опциональные поля
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = None  # "RUB", "USD", etc.
    salary_text: Optional[str] = None  # "от 200 000 до 300 000 руб."
    location: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    experience: Optional[str] = None  # "1-3 года", "от 3 лет"
    employment_type: Optional[str] = None  # "full", "part", "project"
    schedule: Optional[str] = None  # "fullDay", "remote", "flexible"
    
    # Метаданные
    published_at: Optional[str] = None  # ISO format
    source_metadata: Dict[str, Any] = None  # Дополнительные данные из источника
    
    # Внутренние поля системы
    score: float = 0.0  # Оценка соответствия резюме
    applied: bool = False
    cover_letter: Optional[str] = None
    applied_at: Optional[str] = None

class VacancySource(ABC):
    """Абстрактный класс для источника вакансий"""
    
    def __init__(self, config: VacancySourceConfig):
        self.config = config
        self.name = config.name
    
    @abstractmethod
    async def login(self) -> bool:
        """Авторизация в источнике (если требуется)"""
        pass
    
    @abstractmethod
    async def search_vacancies(
        self, 
        query: str, 
        location: str,
        filters: Dict[str, Any]
    ) -> List[UnifiedVacancy]:
        """Поиск вакансий по запросу"""
        pass
    
    @abstractmethod
    async def get_vacancy_details(self, vacancy: UnifiedVacancy) -> UnifiedVacancy:
        """Получение детальной информации о вакансии"""
        pass
    
    @abstractmethod
    async def apply_to_vacancy(
        self, 
        vacancy: UnifiedVacancy, 
        cover_letter: str
    ) -> bool:
        """Отправка отклика на вакансию"""
        pass
    
    @abstractmethod
    async def check_application_status(self, vacancy: UnifiedVacancy) -> str:
        """Проверка статуса отклика (если поддерживается)"""
        pass
```

### 2.2 Реализации источников

#### 2.2.1 HeadHunter Source (Browser-based)

**Класс `HeadHunterBrowserSource`:**

```python
class HeadHunterBrowserSource(VacancySource):
    """Источник HeadHunter через browser automation"""
    
    def __init__(self, config: VacancySourceConfig, browser_tools: dict):
        super().__init__(config)
        self.browser_tools = browser_tools
        self.base_url = "https://hh.ru"
        self.logged_in = False
    
    async def login(self) -> bool:
        """Логин на HH через браузер"""
        # Использует существующую логику из browser_agent_node
        # Адаптирует под новый интерфейс
        pass
    
    async def search_vacancies(self, query, location, filters) -> List[UnifiedVacancy]:
        """Поиск вакансий на HH"""
        # Использует browser_tools для навигации
        # Парсит результаты в UnifiedVacancy
        pass
    
    async def apply_to_vacancy(self, vacancy, cover_letter) -> bool:
        """Отклик на вакансию через браузер"""
        # Использует существующую логику отклика
        pass
```

**Особенности:**
- Использует Playwright MCP tools
- Парсинг через browser_snapshot
- Сохранение специфичных селекторов HH в конфигурации

#### 2.2.2 SuperJob Source (API-based)

**Класс `SuperJobAPISource`:**

```python
import aiohttp
from typing import List, Dict, Any

class SuperJobAPISource(VacancySource):
    """Источник SuperJob через API"""
    
    def __init__(self, config: VacancySourceConfig):
        super().__init__(config)
        self.api_key = config.credentials.get("api_key")
        self.base_url = "https://api.superjob.ru/2.0"
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получает или создает HTTP сессию"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def login(self) -> bool:
        """API не требует логина, но проверяем ключ"""
        if not self.api_key:
            return False
        # Можно проверить валидность ключа через тестовый запрос
        return True
    
    async def search_vacancies(
        self, 
        query: str, 
        location: str,
        filters: Dict[str, Any]
    ) -> List[UnifiedVacancy]:
        """Поиск вакансий через SuperJob API"""
        session = await self._get_session()
        
        # Маппинг параметров поиска
        params = {
            "keyword": query,
            "town": self._map_location_to_sj_id(location),
            "count": filters.get("count", 20),
            "page": filters.get("page", 0),
        }
        
        # Добавляем фильтры если есть
        if "experience" in filters:
            params["experience"] = self._map_experience(filters["experience"])
        if "employment" in filters:
            params["employment"] = self._map_employment(filters["employment"])
        
        headers = {
            "X-Api-App-Id": self.api_key
        }
        
        async with session.get(
            f"{self.base_url}/vacancies/",
            params=params,
            headers=headers
        ) as response:
            data = await response.json()
            
            # Конвертируем в UnifiedVacancy
            vacancies = []
            for item in data.get("objects", []):
                vacancy = self._convert_to_unified(item)
                vacancies.append(vacancy)
            
            return vacancies
    
    def _convert_to_unified(self, sj_vacancy: Dict) -> UnifiedVacancy:
        """Конвертирует вакансию SuperJob в UnifiedVacancy"""
        return UnifiedVacancy(
            source="superjob",
            source_id=str(sj_vacancy.get("id")),
            url=sj_vacancy.get("link", ""),
            title=sj_vacancy.get("profession", ""),
            company=sj_vacancy.get("client", {}).get("title", ""),
            salary_min=sj_vacancy.get("payment_from"),
            salary_max=sj_vacancy.get("payment_to"),
            salary_currency=sj_vacancy.get("currency", "RUB"),
            salary_text=self._format_salary(sj_vacancy),
            location=sj_vacancy.get("town", {}).get("title", ""),
            description=sj_vacancy.get("candidat", ""),
            experience=self._map_experience_from_sj(sj_vacancy.get("experience", {})),
            employment_type=self._map_employment_from_sj(sj_vacancy.get("type_of_work", {})),
            published_at=sj_vacancy.get("date_published"),
            source_metadata=sj_vacancy
        )
    
    async def apply_to_vacancy(self, vacancy: UnifiedVacancy, cover_letter: str) -> bool:
        """Отклик через SuperJob API (если поддерживается)"""
        # SuperJob API может не поддерживать отклики через API
        # В этом случае можно использовать browser automation
        # или возвращать False и использовать fallback
        return False
    
    def _map_location_to_sj_id(self, location: str) -> int:
        """Маппинг названия города в ID SuperJob"""
        # Словарь маппинга или API для получения ID
        location_map = {
            "Москва": 4,
            "Санкт-Петербург": 3,
            # ...
        }
        return location_map.get(location, 4)  # По умолчанию Москва
```

**Особенности:**
- Использует HTTP клиент (aiohttp)
- Не требует browser automation для поиска
- Может потребоваться browser для откликов (если API не поддерживает)

#### 2.2.3 Гибридный источник (API + Browser)

**Класс `HybridVacancySource`:**

```python
class HybridVacancySource(VacancySource):
    """Гибридный источник: API для поиска, browser для откликов"""
    
    def __init__(self, api_source: VacancySource, browser_source: VacancySource):
        self.api_source = api_source
        self.browser_source = browser_source
        self.config = api_source.config
    
    async def search_vacancies(self, query, location, filters):
        """Использует API для быстрого поиска"""
        return await self.api_source.search_vacancies(query, location, filters)
    
    async def apply_to_vacancy(self, vacancy, cover_letter):
        """Использует browser для отклика"""
        return await self.browser_source.apply_to_vacancy(vacancy, cover_letter)
```

## 3. Менеджер источников

### 3.1 Класс `VacancySourceManager`

```python
from typing import Dict, List, Optional
import asyncio

class VacancySourceManager:
    """Менеджер для работы с множественными источниками вакансий"""
    
    def __init__(self, sources_config: List[VacancySourceConfig], browser_tools: dict = None):
        self.sources: Dict[str, VacancySource] = {}
        self.browser_tools = browser_tools
        self._initialize_sources(sources_config)
    
    def _initialize_sources(self, configs: List[VacancySourceConfig]):
        """Инициализирует источники из конфигурации"""
        for config in configs:
            if not config.enabled:
                continue
            
            if config.name == "hh" and config.method == "browser":
                self.sources["hh"] = HeadHunterBrowserSource(config, self.browser_tools)
            elif config.name == "superjob" and config.method == "api":
                self.sources["superjob"] = SuperJobAPISource(config)
            # Добавление других источников...
    
    async def login_all(self) -> Dict[str, bool]:
        """Авторизация во всех источниках"""
        results = {}
        for name, source in self.sources.items():
            try:
                results[name] = await source.login()
            except Exception as e:
                logger.error(f"Ошибка логина в {name}: {e}")
                results[name] = False
        return results
    
    async def search_parallel(
        self, 
        query: str, 
        location: str,
        filters: Dict[str, Any],
        sources: Optional[List[str]] = None
    ) -> List[UnifiedVacancy]:
        """Параллельный поиск на нескольких источниках"""
        sources_to_search = sources or list(self.sources.keys())
        
        tasks = []
        for source_name in sources_to_search:
            if source_name in self.sources:
                source = self.sources[source_name]
                task = source.search_vacancies(query, location, filters)
                tasks.append((source_name, task))
        
        # Параллельное выполнение
        results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Объединяем результаты
        all_vacancies = []
        for (source_name, _), result in zip(tasks, results):
            if isinstance(result, Exception):
                logger.error(f"Ошибка поиска в {source_name}: {result}")
                continue
            all_vacancies.extend(result)
        
        # Дедупликация по URL или title+company
        unique_vacancies = self._deduplicate_vacancies(all_vacancies)
        
        return unique_vacancies
    
    def _deduplicate_vacancies(self, vacancies: List[UnifiedVacancy]) -> List[UnifiedVacancy]:
        """Удаляет дубликаты вакансий из разных источников"""
        seen = set()
        unique = []
        
        for vacancy in vacancies:
            # Ключ для дедупликации: URL или title+company
            key = vacancy.url or f"{vacancy.title}_{vacancy.company}"
            if key not in seen:
                seen.add(key)
                unique.append(vacancy)
        
        return unique
    
    async def apply_to_vacancy(
        self, 
        vacancy: UnifiedVacancy, 
        cover_letter: str
    ) -> bool:
        """Отклик на вакансию через соответствующий источник"""
        source_name = vacancy.source
        if source_name not in self.sources:
            logger.error(f"Источник {source_name} не найден")
            return False
        
        source = self.sources[source_name]
        return await source.apply_to_vacancy(vacancy, cover_letter)
    
    def get_source(self, source_name: str) -> Optional[VacancySource]:
        """Получает источник по имени"""
        return self.sources.get(source_name)
```

## 4. Интеграция в существующую систему

### 4.1 Изменения в `AgentState`

```python
class AgentState(TypedDict):
    # ... существующие поля ...
    
    # Новые поля для множественных источников
    vacancy_sources: Dict[str, VacancySource]  # Активные источники
    source_manager: VacancySourceManager  # Менеджер источников
    current_source: Optional[str]  # Текущий активный источник
    search_sources: List[str]  # Список источников для поиска
```

### 4.2 Изменения в `browser_agent_node.py`

**Рефакторинг для работы через абстракцию:**

```python
async def browser_agent_node(state: AgentState, model: ChatOpenAI, tools: list) -> AgentState:
    """Browser Agent с поддержкой множественных источников"""
    
    source_manager = state.get("source_manager")
    if not source_manager:
        # Fallback на старую логику HH
        return await _legacy_hh_browser_agent(state, model, tools)
    
    # Определяем источники для поиска
    search_sources = state.get("search_sources", ["hh"])
    
    # Параллельный поиск на всех источниках
    if state["browser_status"] == "idle" or state["browser_status"] == "search_failed":
        vacancies = await source_manager.search_parallel(
            query=state.get("user_request", ""),
            location=state.get("search_settings", {}).get("city", "Москва"),
            filters=state.get("search_settings", {}),
            sources=search_sources
        )
        
        state["vacancies"] = [v.__dict__ for v in vacancies]  # Конвертируем в dict
    
    # Обработка текущей вакансии через соответствующий источник
    current_vacancy = state.get("current_vacancy")
    if current_vacancy:
        source_name = current_vacancy.get("source", "hh")
        source = source_manager.get_source(source_name)
        
        if source:
            # Получаем детали через источник
            unified_vacancy = UnifiedVacancy(**current_vacancy)
            detailed_vacancy = await source.get_vacancy_details(unified_vacancy)
            state["current_vacancy"] = detailed_vacancy.__dict__
    
    # Отклик через источник
    if state["browser_status"] == "ready_to_apply":
        cover_letter = state.get("cover_letter", "")
        unified_vacancy = UnifiedVacancy(**state["current_vacancy"])
        
        success = await source_manager.apply_to_vacancy(unified_vacancy, cover_letter)
        if success:
            state["browser_status"] = "application_sent"
            state["applied_count"] += 1
    
    return state
```

### 4.3 Изменения в `planner_node.py`

**Обновление промпта для множественных источников:**

```python
PLANNER_PROMPT = """
...
Доступные источники вакансий:
{sources_list}

Рекомендации:
- Используй несколько источников для расширения поиска
- Учитывай особенности каждого источника при планировании
...
"""
```

### 4.4 Изменения в `main.py`

**Инициализация менеджера источников:**

```python
async def main():
    # ... существующий код ...
    
    # Загрузка конфигурации источников
    config = load_config()
    sources_config = config.get("vacancy_sources", [])
    
    # Инициализация менеджера источников
    source_manager = VacancySourceManager(
        sources_config=sources_config,
        browser_tools=browser_tools  # Из MCP клиента
    )
    
    # Авторизация во всех источниках
    login_results = await source_manager.login_all()
    logger.info(f"Авторизация: {login_results}")
    
    # Создание начального состояния с менеджером
    initial_state = create_initial_state(
        # ... параметры ...
        source_manager=source_manager,
        search_sources=config.get("search_sources", ["hh"])
    )
    
    # ... остальной код ...
```

## 5. Конфигурация

### 5.1 Структура `config.json`

```json
{
  "vacancy_sources": [
    {
      "name": "hh",
      "enabled": true,
      "method": "browser",
      "credentials": {
        "login": "user@example.com",
        "password": "password123"
      },
      "search_params": {
        "default_city": "Москва",
        "default_experience": "between1And3"
      }
    },
    {
      "name": "superjob",
      "enabled": true,
      "method": "api",
      "credentials": {
        "api_key": "your_superjob_api_key"
      },
      "search_params": {
        "default_town": 4,
        "default_count": 20
      }
    }
  ],
  "search_settings": {
    "sources": ["hh", "superjob"],
    "parallel_search": true,
    "deduplicate": true,
    "max_vacancies_per_source": 50
  },
  "hh_credentials": {
    "login": "user@example.com",
    "password": "password123"
  }
}
```

### 5.2 Маппинг параметров поиска

**Модуль `mas/source_mappers.py`:**

```python
"""Маппинг параметров поиска между источниками"""

# Маппинг городов
CITY_MAP = {
    "Москва": {
        "hh": "Москва",
        "superjob": 4,
        "habr": "moscow"
    },
    "Санкт-Петербург": {
        "hh": "Санкт-Петербург",
        "superjob": 3,
        "habr": "spb"
    }
}

# Маппинг опыта работы
EXPERIENCE_MAP = {
    "noExperience": {
        "hh": "noExperience",
        "superjob": 1,  # Без опыта
    },
    "between1And3": {
        "hh": "between1And3",
        "superjob": 2,  # От 1 года
    }
}

def map_search_params(source: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Маппит параметры поиска для конкретного источника"""
    mapped = params.copy()
    
    # Маппинг города
    if "city" in params:
        city = params["city"]
        if city in CITY_MAP and source in CITY_MAP[city]:
            mapped["city"] = CITY_MAP[city][source]
    
    # Маппинг опыта
    if "experience" in params:
        exp = params["experience"]
        if exp in EXPERIENCE_MAP and source in EXPERIENCE_MAP[exp]:
            mapped["experience"] = EXPERIENCE_MAP[exp][source]
    
    return mapped
```

## 6. Хранение в ChromaDB

### 6.1 Обновление структуры метаданных

**В `chroma_utils.py`:**

```python
async def store_vacancy(
    chroma_tools: dict,
    vacancy: UnifiedVacancy,  # Изменено с dict на UnifiedVacancy
    session_id: str
) -> bool:
    """Сохраняет вакансию в Chroma с указанием источника"""
    
    metadata = {
        "source": vacancy.source,  # Новое поле
        "source_id": vacancy.source_id,
        "url": vacancy.url,
        "title": vacancy.title,
        "company": vacancy.company,
        "session_id": session_id,
        # ... остальные поля ...
    }
    
    # ...
```

### 6.2 Поиск с фильтрацией по источнику

```python
async def search_similar_vacancies(
    chroma_tools: dict,
    query_text: str,
    sources: Optional[List[str]] = None,  # Фильтр по источникам
    n_results: int = 5
) -> List[Dict[str, Any]]:
    """Поиск с возможностью фильтрации по источникам"""
    
    query_params = {
        "collection_name": COLLECTION_VACANCIES,
        "query_texts": [query_text],
        "n_results": n_results,
    }
    
    if sources:
        query_params["where"] = {"source": {"$in": sources}}
    
    # ...
```

## 7. Обработка ошибок и fallback

### 7.1 Стратегия fallback

```python
class VacancySourceManager:
    async def search_with_fallback(
        self,
        query: str,
        location: str,
        filters: Dict[str, Any],
        primary_sources: List[str]
    ) -> List[UnifiedVacancy]:
        """Поиск с fallback на другие источники при ошибках"""
        
        results = []
        failed_sources = []
        
        # Пробуем основные источники
        for source_name in primary_sources:
            try:
                source = self.sources[source_name]
                vacancies = await source.search_vacancies(query, location, filters)
                results.extend(vacancies)
            except Exception as e:
                logger.error(f"Ошибка поиска в {source_name}: {e}")
                failed_sources.append(source_name)
        
        # Если нет результатов, пробуем другие источники
        if not results and failed_sources:
            fallback_sources = [s for s in self.sources.keys() if s not in failed_sources]
            for source_name in fallback_sources:
                try:
                    source = self.sources[source_name]
                    vacancies = await source.search_vacancies(query, location, filters)
                    results.extend(vacancies)
                    break  # Используем первый успешный
                except Exception as e:
                    logger.error(f"Ошибка fallback в {source_name}: {e}")
        
        return results
```

### 7.2 Обработка специфичных ошибок

```python
class SourceError(Exception):
    """Базовое исключение для ошибок источников"""
    pass

class AuthenticationError(SourceError):
    """Ошибка авторизации"""
    pass

class RateLimitError(SourceError):
    """Превышен лимит запросов"""
    pass

class SourceUnavailableError(SourceError):
    """Источник недоступен"""
    pass
```

## 8. Тестирование

### 8.1 Моки для тестирования

```python
class MockVacancySource(VacancySource):
    """Mock источник для тестирования"""
    
    def __init__(self, config: VacancySourceConfig):
        super().__init__(config)
        self.vacancies = []
    
    async def search_vacancies(self, query, location, filters):
        return self.vacancies
    
    async def login(self):
        return True
```

### 8.2 Unit тесты

```python
async def test_source_manager_parallel_search():
    """Тест параллельного поиска"""
    configs = [
        VacancySourceConfig(name="mock1", enabled=True, ...),
        VacancySourceConfig(name="mock2", enabled=True, ...)
    ]
    manager = VacancySourceManager(configs)
    
    results = await manager.search_parallel("Python", "Москва", {})
    assert len(results) > 0
```

## 9. План внедрения

### Этап 1: Создание абстракций
- [ ] Создать базовые классы `VacancySource`, `UnifiedVacancy`
- [ ] Создать `VacancySourceManager`
- [ ] Создать мапперы параметров поиска

### Этап 2: Рефакторинг HH
- [ ] Выделить логику HH в `HeadHunterBrowserSource`
- [ ] Адаптировать существующий код под новый интерфейс
- [ ] Сохранить обратную совместимость

### Этап 3: Интеграция SuperJob
- [ ] Реализовать `SuperJobAPISource`
- [ ] Добавить обработку API ответов
- [ ] Интегрировать в менеджер источников

### Этап 4: Обновление узлов графа
- [ ] Модифицировать `browser_agent_node` для работы с менеджером
- [ ] Обновить `planner_node` для множественных источников
- [ ] Обновить `cover_letter_agent_node` (если нужно)

### Этап 5: Конфигурация и инициализация
- [ ] Обновить `config.json` структуру
- [ ] Модифицировать `main.py` для инициализации менеджера
- [ ] Обновить `create_initial_state`

### Этап 6: Хранение в ChromaDB
- [ ] Обновить `store_vacancy` для работы с `UnifiedVacancy`
- [ ] Добавить фильтрацию по источникам в поиске
- [ ] Обновить метаданные коллекций

### Этап 7: Тестирование
- [ ] Unit тесты для источников
- [ ] Интеграционные тесты для менеджера
- [ ] E2E тесты с реальными источниками

## 10. Расширяемость

### 10.1 Добавление нового источника

**Шаги:**
1. Создать класс, наследующий `VacancySource`
2. Реализовать все абстрактные методы
3. Добавить конфигурацию в `config.json`
4. Зарегистрировать в `VacancySourceManager._initialize_sources`

**Пример для Habr Career:**

```python
class HabrCareerSource(VacancySource):
    """Источник Habr Career"""
    
    async def search_vacancies(self, query, location, filters):
        # Реализация поиска через Habr API или парсинг
        pass
```

### 10.2 Плагинная архитектура (опционально)

```python
class SourceRegistry:
    """Реестр источников для плагинной архитектуры"""
    
    _sources = {}
    
    @classmethod
    def register(cls, name: str, source_class: type):
        cls._sources[name] = source_class
    
    @classmethod
    def create(cls, name: str, config: VacancySourceConfig):
        source_class = cls._sources.get(name)
        if source_class:
            return source_class(config)
        raise ValueError(f"Источник {name} не зарегистрирован")
```

## 11. Производительность

### 11.1 Параллельный поиск

- **Преимущества**: Уменьшение общего времени поиска
- **Риски**: Нагрузка на источники, rate limiting
- **Решение**: Ограничение параллельных запросов, retry с backoff

### 11.2 Кэширование

```python
from functools import lru_cache
import hashlib

class CachedVacancySource(VacancySource):
    """Обертка с кэшированием результатов поиска"""
    
    def __init__(self, source: VacancySource, cache_ttl: int = 3600):
        self.source = source
        self.cache_ttl = cache_ttl
        self._cache = {}
    
    async def search_vacancies(self, query, location, filters):
        cache_key = self._generate_cache_key(query, location, filters)
        
        if cache_key in self._cache:
            cached_result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_result
        
        result = await self.source.search_vacancies(query, location, filters)
        self._cache[cache_key] = (result, time.time())
        return result
```

## 12. Безопасность

### 12.1 Хранение credentials

- Использовать переменные окружения для API ключей
- Шифрование паролей в конфигурации (опционально)
- Не логировать чувствительные данные

### 12.2 Rate limiting

```python
from asyncio import Semaphore

class RateLimitedSource(VacancySource):
    """Обертка с ограничением частоты запросов"""
    
    def __init__(self, source: VacancySource, max_requests_per_minute: int = 60):
        self.source = source
        self.semaphore = Semaphore(max_requests_per_minute)
        self.request_times = []
    
    async def search_vacancies(self, query, location, filters):
        async with self.semaphore:
            # Проверка rate limit
            await self._wait_if_needed()
            return await self.source.search_vacancies(query, location, filters)
```

## 13. Мониторинг и метрики

### 13.1 Метрики источников

- Количество найденных вакансий по источникам
- Время ответа каждого источника
- Количество ошибок по источникам
- Успешность откликов по источникам

### 13.2 Логирование

```python
logger.info(f"🔍 Поиск на источниках: {sources}")
logger.info(f"✅ Найдено вакансий: HH={hh_count}, SJ={sj_count}")
logger.error(f"❌ Ошибка поиска в {source_name}: {error}")
```

## 14. Обратная совместимость

### 14.1 Миграция существующего кода

- Сохранить старую логику HH как fallback
- Постепенная миграция на новую архитектуру
- Флаг `use_new_architecture` для переключения

### 14.2 Конфигурация по умолчанию

```json
{
  "vacancy_sources": [
    {
      "name": "hh",
      "enabled": true,
      "method": "browser"
    }
  ],
  "legacy_hh_mode": false  // Отключить старую логику после миграции
}
```

---

## Резюме

Архитектурный план предусматривает:

1. **Абстракцию источников** через интерфейс `VacancySource`
2. **Унифицированную структуру** вакансий через `UnifiedVacancy`
3. **Менеджер источников** для параллельного поиска и управления
4. **Поддержку разных методов**: browser automation и API
5. **Легкую расширяемость** для добавления новых источников
6. **Обратную совместимость** с существующим кодом HH
7. **Интеграцию с ChromaDB** с указанием источника

План обеспечивает гибкость, масштабируемость и возможность работы с множественными источниками вакансий одновременно.

