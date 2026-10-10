import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
import json

load_dotenv()

SERVERS = { 
    "math": {
        "transport": "stdio",
        "command": "uvx",
        "args": [
            "--from", "fastmcp-slim", # Fixes the executable warning
            "--with", "aiosqlite",    # Injects the missing dependency
            "fastmcp",
            "run",
            r"C:\Users\darsh\Desktop\MCP\Test Remote Server\main.py"
        ]
    },
    # ... keep your expense and manim-server configurations ...
}

async def main():
    
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()


    named_tools = {}
    for tool in tools:
        named_tools[tool.name] = tool

    print("Available tools:", named_tools.keys())

    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    llm_with_tools = llm.bind_tools(tools)

    prompt = "Draw a triangle rotating in place using the manim tool."
    # prompt = "Calculate the sum of 1 and 2"
    response = await llm_with_tools.ainvoke(prompt)

    if not getattr(response, "tool_calls", None):
        print("\nLLM Reply:", response.content)
        return

    tool_messages = []
    for tc in response.tool_calls:
        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]

        result = await named_tools[selected_tool].ainvoke(selected_tool_args)
        tool_messages.append(ToolMessage(tool_call_id=selected_tool_id, content=json.dumps(result)))
        

    final_response = await llm_with_tools.ainvoke([prompt, response, *tool_messages])
    print(f"Final response: {final_response.content}")


if __name__ == '__main__':
    asyncio.run(main())