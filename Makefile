.PHONY: help chroma-start chroma-stop chroma-clean chroma-restart chroma-status

help:
	@echo "==================================================="
	@echo "📋 Makefile для Job Searcher Agent"
	@echo "==================================================="
	@echo ""
	@echo "Команды для управления Chroma MCP Server:"
	@echo "  make chroma-start    - Запустить Chroma MCP Server"
	@echo "  make chroma-stop     - Остановить Chroma MCP Server"
	@echo "  make chroma-restart  - Перезапустить Chroma MCP Server"
	@echo "  make chroma-clean    - Очистить данные Chroma"
	@echo "  make chroma-status   - Проверить статус Chroma"
	@echo ""
	@echo "Основные команды:"
	@echo "  make run             - Запустить агент"
	@echo "  make test            - Запустить тесты"
	@echo "  make clean           - Очистить временные файлы"
	@echo ""
	@echo "==================================================="

# Chroma MCP Server управление
chroma-start:
	@echo "🚀 Запуск Chroma MCP Server..."
	@mkdir -p ./chroma_data
	@mkdir -p ./logs
	@echo "📁 Директория для данных: ./chroma_data"
	@echo "📝 Логи: ./logs/chroma_mcp_*.log"
	@nohup uv run chroma-mcp-server \
		--mode http \
		--host 0.0.0.0 \
		--port 8091 \
		--client-type persistent \
		--data-dir ./chroma_data \
		--log-dir ./logs \
		--log-level INFO \
		> ./logs/chroma_mcp_server.log 2>&1 & echo $$! > ./logs/chroma.pid
	@sleep 2
	@if [ -f ./logs/chroma.pid ]; then \
		echo "✅ Chroma MCP Server запущен (PID: $$(cat ./logs/chroma.pid))"; \
		echo "🌐 Адрес: http://0.0.0.0:8091"; \
		echo "📡 SSE endpoint: http://localhost:8091/sse"; \
	else \
		echo "❌ Ошибка запуска Chroma MCP Server"; \
		echo "📋 Проверьте логи: tail -f ./logs/chroma_mcp_server.log"; \
	fi

chroma-stop:
	@echo "🛑 Остановка Chroma MCP Server..."
	@if [ -f ./logs/chroma.pid ]; then \
		kill $$(cat ./logs/chroma.pid) 2>/dev/null || true; \
		rm -f ./logs/chroma.pid; \
		echo "✅ Chroma MCP Server остановлен"; \
	else \
		echo "⚠️  PID файл не найден. Пытаемся найти процесс..."; \
		pkill -f "chroma-mcp-server" || echo "Процесс не найден"; \
	fi

chroma-restart: chroma-stop
	@sleep 2
	@$(MAKE) chroma-start

chroma-clean:
	@echo "🧹 Очистка данных Chroma..."
	@read -p "Вы уверены? Все данные будут удалены [y/N]: " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		rm -rf ./chroma_data; \
		echo "✅ Данные Chroma удалены"; \
	else \
		echo "❌ Отменено"; \
	fi

chroma-status:
	@echo "📊 Проверка статуса Chroma MCP Server..."
	@if [ -f ./logs/chroma.pid ]; then \
		PID=$$(cat ./logs/chroma.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "✅ Chroma MCP Server запущен (PID: $$PID)"; \
			echo "🌐 Адрес: http://0.0.0.0:8091"; \
		else \
			echo "❌ Процесс не найден (PID: $$PID устарел)"; \
			rm -f ./logs/chroma.pid; \
		fi; \
	else \
		echo "⚠️  Chroma MCP Server не запущен"; \
	fi

# Основные команды проекта
run:
	@echo "🚀 Запуск Job Searcher Agent..."
	uv run python main.py

test:
	@echo "🧪 Запуск тестов..."
	PYTHONPATH=. uv run pytest tests/ -v

clean:
	@echo "🧹 Очистка временных файлов..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Очистка завершена"


