"""Petit client MCP pour tester le serveur sans Claude Desktop.

Depuis la racine du projet :
    python -m src.try_mcp_client "How many violent events were recorded in North Africa in 2025?"
"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main(question):
    params = StdioServerParameters(command=sys.executable, args=["-m", "src.mcp_server"])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Outils proposés par le serveur :")
            for tool in tools.tools:
                print(f"  - {tool.name}")

            docs = await session.call_tool("list_documents", {})
            print("\nDocuments indexés :\n" + docs.content[0].text)

            result = await session.call_tool("search_papers", {"question": question, "k": 3})
            print(f"\nRésultat de search_papers({question!r}, k=3) :\n")
            print(result.content[0].text)


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "How many violent events were recorded in North Africa in 2025?"
    asyncio.run(main(question))