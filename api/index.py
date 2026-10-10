import os
import json
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
# Hardcoded API key to ensure zero environment variable missing issues
OPENROUTER_API_KEY = "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"
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

def ask_openrouter(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Explicit headers with exact formatting
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vercel.com",
        "X-Title": "Level 6 AI Engine"
    }
    
    payload = {
        "model": "deepseek/deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    data_bytes = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
    
    try:
        response = urllib.request.urlopen(req, timeout=25)
        res_text = response.read().decode('utf-8')
        res_data = json.loads(res_text)
        
        if "choices" in res_data and len(res_data["choices"]) > 0:
            return res_data["choices"][0]["message"]["content"]
        else:
            return f"Unexpected response structure: {res_text[:200]}"
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        return f"OpenRouter HTTP Error {e.code}: {error_body}"
    except Exception as e:
        return f"OpenRouter Request Error: {str(e)}"

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write("Level 6 Autonomous AI Engine (OpenRouter Fixed) is Active!".encode('utf-8'))

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
                        "🔥 *Level 6 Autonomous AI Engine (OpenRouter) ONLINE!*\n\n"
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
                    send_telegram_message(chat_id, "🧠 *AI Boardroom* is analyzing your request via OpenRouter...")
                    prompt = f"Act as an expert AI Boardroom (CEO, CTO, CMO). Provide top strategic advice for: {query}"
                    ai_reply = ask_openrouter(prompt)
                    send_telegram_message(chat_id, ai_reply)

                elif text.startswith("/lead"):
                    query = text.replace("/lead", "").strip()
                    if not query:
                        query = "Digital marketing clients"
                    send_telegram_message(chat_id, f"🔍 Searching live data for leads: `{query}`...")
                    search_results = search_tavily(query)
                    prompt = f"Analyze these search results and format them into clear, actionable business leads/prospects:\n\n{search_results}"
                    ai_reply = ask_openrouter(prompt)
                    send_telegram_message(chat_id, ai_reply)

                elif text.startswith("/blog"):
                    query = text.replace("/blog", "").strip()
                    if not query:
                        query = "Future of AI automation"
                    send_telegram_message(chat_id, "✍️ Drafting SEO blog post...")
                    prompt = f"Write a professional, engaging SEO-optimized blog post with headings about: {query}"
                    ai_reply = ask_openrouter(prompt)
                    send_telegram_message(chat_id, ai_reply)
                
                else:
                    send_telegram_message(chat_id, f"🤖 Engine Received: {text}\nUse /start to see available commands.")

        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode('utf-8'))
