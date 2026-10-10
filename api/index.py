import os
import json
import requests
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Level 6 Autonomous Engine API is Active!".encode('utf-8'))

    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length)
        
        try:
            data = json.loads(body.decode('utf-8'))
            
            if "message" in data:
                message = data["message"]
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")

                if text.startswith("/start"):
                    reply = "🔥 Level 6 Autonomous AI Engine is ONLINE!\n\nAvailable commands:\n/board [topic]\n/lead [query]\n/blog [topic]"
                    send_telegram_message(chat_id, reply)
                elif text:
                    reply = f"🤖 Engine Received: {text}\n\nProcessing your request..."
                    send_telegram_message(chat_id, reply)

        except Exception as e:
            print(f"Error processing webhook: {e}")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
