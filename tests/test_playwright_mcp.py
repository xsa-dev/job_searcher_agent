import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters import load_mcp_tools

async def test():
    client = MultiServerMCPClient({
        "playwright": {
            "command": "npx",
            "args": ["-y", "@playwright/mcp@latest"],
            "transport": "stdio",
        }
    })
    
    try:
        async with client.session("playwright") as session:
            tools = await load_mcp_tools(session=session, server_name="playwright")
            print(f"✅ Загружено {len(tools)} инструментов:")
            for tool in tools:
                print(f"  - {tool.name}")
    except* Exception as eg:
        for exc in eg.exceptions:
            if "BrokenResourceError" in type(exc).__name__ or "ValidationError" in str(exc):
                print(f"⚠️ Игнорируем: {type(exc).__name__}")
            else:
                print(f"❌ Ошибка: {exc}")

asyncio.run(test())
