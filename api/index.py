import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") # You can use OpenRouter or Gemini key here
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")

def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def search_tavily(query):
    if not TAVILY_API_KEY:
        return "Tavily API key not configured."
    url = "https://api.tavily.com/search"
    payload = json.dumps({
        "api_key": TAVILY_API_KEY,
        "query": query,
        "max_results": 3
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        response = urllib.request.urlopen(req, timeout=10)
        data = json.loads(response.read().decode('utf-8'))
        results = data.get("results", [])
        summary = ""
        for r in results:
            summary += f"- [{r.get('title')}]({r.get('url')})\n{r.get('content')}\n\n"
        return summary if summary else "No relevant search results found."
    except Exception as e:
        return f"Search error: {e}"

def ask_ai(prompt):
    if not GEMINI_API_KEY:
        return "API key not configured."
    
    # Using Google's alternative generative language endpoint structure or OpenRouter if preferred
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    
    # Let's fallback to a direct text generation payload
    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    
    try:
        response = urllib.request.urlopen(req, timeout=15)
        res_data = json.loads(response.read().decode('utf-8'))
        
        if "candidates" in res_data and len(res_data["candidates"]) > 0:
            parts = res_data["candidates"][0]["content"]["parts"]
            if len(parts) > 0 and "text" in parts[0]:
                return parts[0]["text"]
        return "No text generated."
            
    except urllib.error.HTTPError as e:
        # Fallback public free model simulation or direct error description
        return f"API Error ({e.code}): Check model parameters or switch to OpenRouter."
    except Exception as e:
        return f"Request Error: {e}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Level 6 Autonomous AI Engine is Active!".encode('utf-8'))

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            data = json.loads(body.decode('utf-8'))
            
            if "message" in data:
                message = data["message"]
                chat_id = message.get("chat", {}).get("id")
                text = message.get("text", "")

                if text.startswith("/start"):
                    reply = (
                        "🔥 *Level 6 Autonomous AI Engine is ONLINE!*\n\n"
                        "Available commands:\n"
                        "👉 `/board [topic]` - AI Boardroom Strategy\n"
                        "👉 `/lead [query]` - Tavily Lead Generation\n"
                        "👉 `/blog [topic]` - SEO Blog Post Generator"
                    )
                    send_telegram_message(chat_id, reply)
                
                elif text.startswith("/board"):
                    query = text.replace("/board", "").strip()
                    if not query:
                        query = "General business growth strategy"
                    send_telegram_message(chat_id, "🧠 *AI Boardroom* is analyzing your request...")
                    prompt = f"Act as an expert AI Boardroom (CEO, CTO, CMO). Provide top strategic advice for: {query}"
                    ai_reply = ask_ai(prompt)
                    send_telegram_message(chat_id, ai_reply)

                elif text.startswith("/lead"):
                    query = text.replace("/lead", "").strip()
                    if not query:
                        query = "Digital marketing clients"
                    send_telegram_message(chat_id, f"🔍 Searching live data for leads: `{query}`...")
                    search_results = search_tavily(query)
                    prompt = f"Analyze these search results and format them into clear, actionable business leads/prospects:\n\n{search_results}"
                    ai_reply = ask_ai(prompt)
                    send_telegram_message(chat_id, ai_reply)

                elif text.startswith("/blog"):
                    query = text.replace("/blog", "").strip()
                    if not query:
                        query = "Future of AI automation"
                    send_telegram_message(chat_id, "✍️ Drafting SEO blog post...")
                    prompt = f"Write a professional, engaging SEO-optimized blog post with headings about: {query}"
                    ai_reply = ask_ai(prompt)
                    send_telegram_message(chat_id, ai_reply)
                
                else:
                    send_telegram_message(chat_id, f"🤖 Engine Received: {text}\nUse /start to see available commands.")

        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
