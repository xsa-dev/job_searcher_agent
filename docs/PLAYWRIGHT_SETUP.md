# Playwright MCP Setup Guide

## Что такое Playwright MCP

Playwright MCP (@playwright/mcp@latest) - это MCP сервер для автоматизации браузера с использованием Playwright. Он предоставляет современный API для веб-автоматизации с поддержкой множества браузеров.

## Установка

1. Установите Playwright MCP Server через npm:
   ```bash
   npx -y @playwright/mcp@latest
   ```

2. Убедитесь, что Node.js версии 18+ установлен:
   ```bash
   node --version
   ```

## Использование

### Доступные инструменты:

#### Навигация и просмотр
- `Playwright_navigate(url, browserType, width, height, headless, timeout, waitUntil)` - Переход на URL с настройками браузера
- `playwright_get_visible_text()` - Получить видимый текст страницы
- `playwright_get_visible_html()` - Получить HTML содержимое страницы

#### Взаимодействие с элементами
- `Playwright_click(selector)` - Клик по элементу (CSS селектор)
- `Playwright_fill(selector, value)` - Заполнить поле ввода
- `Playwright_select(selector, value)` - Выбрать значение в dropdown
- `Playwright_hover(selector)` - Навести курсор на элемент
- `playwright_click_and_switch_tab(selector)` - Кликнуть и переключиться на новую вкладку
- `playwright_upload_file(selector, filePath)` - Загрузить файл

#### Работа с iframe
- `Playwright_iframe_click(iframeSelector, selector)` - Клик в iframe
- `Playwright_iframe_fill(iframeSelector, selector, value)` - Заполнить поле в iframe

#### Скриншоты и отладка
- `Playwright_screenshot(name, selector, width, height, fullPage, savePng, downloadsDir)` - Сделать скриншот
- `Playwright_console_logs(search, limit, type, clear)` - Получить логи консоли

#### Расширенные возможности
- `Playwright_evaluate(script)` - Выполнить JavaScript код на странице
- `Playwright_close()` - Закрыть браузер
- `Playwright_expect_response(id, url)` - Ожидать HTTP ответ
- `Playwright_assert_response(id, value)` - Проверить HTTP ответ
- `playwright_custom_user_agent(userAgent)` - Установить User Agent

#### Генерация кода
- `start_codegen_session(options)` - Начать запись действий для генерации кода
- `end_codegen_session(sessionId)` - Завершить запись и сгенерировать тест
- `get_codegen_session(sessionId)` - Получить информацию о сессии записи
- `clear_codegen_session(sessionId)` - Очистить сессию без генерации

## Пример использования

```python
from langchain_mcp import MCPClient, load_mcp_tools

# Инициализация клиента
client = MCPClient(
    {
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
            "transport": "stdio",
        }
    }
)

async with client.session("playwright") as session:
    # Загрузка инструментов
    tools = await load_mcp_tools(session=session, server_name="playwright")
    
    # Использование инструментов
    # tools будет содержать все доступные Playwright инструменты
```

## Важно:

1. **Селекторы**: Используйте CSS селекторы для идентификации элементов
2. **Асинхронность**: Все инструменты асинхронные, используйте `await`
3. **Ошибки**: Playwright автоматически ожидает элементы (timeout по умолчанию)
4. **Браузеры**: Поддерживает Chromium (по умолчанию), Firefox и WebKit

## Отличия от BrowserMCP

| Aspect | BrowserMCP | Playwright MCP |
|--------|------------|----------------|
| Технология | Расширение браузера | Playwright API |
| Установка | Расширение Chrome | npm пакет |
| Браузеры | Только Chrome | Chromium, Firefox, WebKit |
| API | browser_* | Playwright_* и playwright_* |
| Стабильность | Требует расширение | Встроенная автоматизация |
| Функции | Базовые | Расширенные (iframe, file upload, и т.д.) |

## Troubleshooting

### Ошибка "Cannot find module"
```bash
npm cache clean --force
npx -y @playwright/mcp@latest
```

### Браузер не запускается
Убедитесь, что установлены браузеры Playwright:
```bash
npx playwright install
```

### Timeout ошибки
Увеличьте timeout в параметрах `Playwright_navigate`:
```python
{"url": "https://example.com", "timeout": 60000}  # 60 секунд
```

## Дополнительные ресурсы

- [Официальная документация](https://executeautomation.github.io/mcp-playwright/)
- [GitHub репозиторий](https://github.com/executeautomation/mcp-playwright)
- [Playwright документация](https://playwright.dev/)

