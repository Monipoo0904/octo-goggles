"""
Vercel API Handler for MCP Server with ChatGPT
Exposes MCP server functionality via HTTP endpoints
"""

from http.server import BaseHTTPRequestHandler
import json
import os
from openai import OpenAI

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to the API."""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            action = data.get('action')
            
            if action == 'chat':
                response = self.handle_chat(data)
            elif action == 'analyze':
                response = self.handle_analyze(data)
            elif action == 'list_tools':
                response = self.handle_list_tools()
            else:
                response = {'error': 'Unknown action'}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        """Handle GET requests."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            'status': 'online',
            'service': 'MCP ChatGPT Server',
            'endpoints': {
                'POST /api': 'Main API endpoint',
                'actions': ['chat', 'analyze', 'list_tools']
            }
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_chat(self, data):
        """Handle chat requests."""
        message = data.get('message', '')
        system_prompt = data.get('system_prompt', 'You are a helpful AI assistant.')
        model = data.get('model', 'gpt-4o')
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=1000
            )
            
            return {
                'success': True,
                'response': response.choices[0].message.content,
                'model': model,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_analyze(self, data):
        """Handle text analysis requests."""
        text = data.get('text', '')
        analysis_type = data.get('analysis_type', 'summary')
        
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
                    {"role": "user", "content": prompts.get(analysis_type, prompts['summary'])}
                ],
                max_tokens=1000
            )
            
            return {
                'success': True,
                'analysis': response.choices[0].message.content,
                'type': analysis_type,
                'usage': {
                    'prompt_tokens': response.usage.prompt_tokens,
                    'completion_tokens': response.usage.completion_tokens,
                    'total_tokens': response.usage.total_tokens
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def handle_list_tools(self):
        """Return available tools."""
        return {
            'success': True,
            'tools': [
                {
                    'name': 'chat',
                    'description': 'Chat with ChatGPT',
                    'parameters': ['message', 'system_prompt (optional)', 'model (optional: gpt-4o, gpt-4o-mini, gpt-4-turbo)']
                },
                {
                    'name': 'analyze',
                    'description': 'Analyze text',
                    'parameters': ['text', 'analysis_type (sentiment|themes|summary|key_points)']
                }
            ]
        }