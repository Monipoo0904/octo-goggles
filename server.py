"""
MCP Server with ChatGPT Integration
A Model Context Protocol server that connects to ChatGPT via OpenAI API
"""

import asyncio
from typing import Any
from mcp.server import Server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)
import mcp.server.stdio
from openai import OpenAI
import os

# Initialize the MCP server
app = Server("chatgpt-mcp-server")

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="chat_with_gpt",
            description="Send a message to ChatGPT and get a response. Use this for general conversations, questions, analysis, or any task requiring AI assistance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "The message or prompt to send to ChatGPT"
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Optional system prompt to guide ChatGPT's behavior",
                        "default": ""
                    },
                    "model": {
                        "type": "string",
                        "description": "GPT model to use",
                        "enum": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"],
                        "default": "gpt-4o"
                    }
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="analyze_text",
            description="Analyze text for sentiment, themes, or specific patterns using ChatGPT",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["sentiment", "themes", "summary", "key_points"],
                        "description": "Type of analysis to perform"
                    }
                },
                "required": ["text", "analysis_type"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "chat_with_gpt":
        message = arguments.get("message")
        system_prompt = arguments.get("system_prompt", "You are a helpful AI assistant.")
        model = arguments.get("model", "gpt-4o")
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error calling ChatGPT: {str(e)}")]
    
    elif name == "analyze_text":
        text = arguments.get("text")
        analysis_type = arguments.get("analysis_type")
        
        prompts = {
            "sentiment": f"Analyze the sentiment of this text and provide a detailed assessment:\n\n{text}",
            "themes": f"Identify and explain the main themes in this text:\n\n{text}",
            "summary": f"Provide a concise summary of this text:\n\n{text}",
            "key_points": f"Extract the key points from this text as a bulleted list:\n\n{text}"
        }
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": prompts[analysis_type]}
                ],
                max_tokens=1000
            )
            
            result = response.choices[0].message.content
            return [TextContent(type="text", text=result)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error analyzing text: {str(e)}")]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server using stdio transport."""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())