.PHONY: help chroma-start chroma-stop chroma-clean chroma-restart chroma-status

help:
	@echo "==================================================="
	@echo "📋 Makefile для Job Searcher Agent"
	@echo "==================================================="
	@echo "Основные команды:"
	@echo "  make run             - Запустить агент"
	@echo "  make test            - Запустить тесты"
	@echo "  make clean           - Очистить временные файлы"
	@echo ""
	@echo "==================================================="

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
