import json
import os
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai
import requests

# --- ENVIRONMENT VARIABLES ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WP_URL = os.getenv("WP_URL")
WP_USER = os.getenv("WP_USER")
WP_APPLICATION_PASSWORD = os.getenv("WP_APPLICATION_PASSWORD")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

AGENT_REGISTRY = {
    "CMO": (
        "You are Chief Marketing Officer. Focus on SEO, growth, and customer"
        " acquisition."
    ),
    "CFO": (
        "You are Chief Financial Officer. Focus on ROI, profit margins, and"
        " pricing strategy."
    ),
    "CTO": (
        "You are Chief Technology Officer. Focus on scalable backend, APIs, and"
        " tech stack."
    ),
    "LEGAL": (
        "You are Chief Legal Officer. Focus on copyright compliance and terms"
        " of service."
    ),
}


def search_tavily(query):
    if not TAVILY_API_KEY:
        return "Tavily API key missing."
    try:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "advanced",
            "max_results": 3,
        }
        res = requests.post(url, json=payload, timeout=10)
        data = res.json()
        results = data.get("results", [])
        formatted = ""
        for idx, item in enumerate(results, 1):
            formatted += f"\n[{idx}] {item.get('title')}\nURL: {item.get('url')}\nContent: {item.get('content')}\n"
        return formatted or "No relevant search results."
    except Exception as e:
        return f"Search Error: {str(e)}"


def post_to_wordpress(title, content_html):
    if not (WP_URL and WP_USER and WP_APPLICATION_PASSWORD):
        return "WordPress envs not set."
    try:
        post_data = {
            "title": title,
            "content": content_html,
            "status": "publish",
        }
        res = requests.post(
            WP_URL,
            json=post_data,
            auth=(WP_USER, WP_APPLICATION_PASSWORD),
            timeout=15,
        )
        if res.status_code in [200, 201]:
            return f"Published! Link: {res.json().get('link', '')}"
        return f"WP Failed: {res.text}"
    except Exception as e:
        return f"WP Error: {str(e)}"


def generate_ai_response(user_text):
    model = genai.GenerativeModel("gemini-1.5-flash")

    if user_text.lower().startswith("/board "):
        topic = user_text[7:].strip()
        search_data = search_tavily(topic)
        report = f"🏛️ **AI BOARDROOM REPORT**\n**Topic:** {topic}\n\n"
        for agent_key in ["CMO", "CTO", "CFO", "LEGAL"]:
            persona = AGENT_REGISTRY[agent_key]
            prompt = f"Role: {persona}\nResearch: {search_data}\nEvaluate topic '{topic}' in 3 points."
            res = model.generate_content(prompt)
            report += f"👔 **{agent_key}:**\n{res.text.strip()}\n\n"
        return report

    elif user_text.lower().startswith("/blog "):
        topic = user_text[6:].strip()
        search_data = search_tavily(topic)
        prompt = f"Write an SEO blog on '{topic}' using HTML tags (<h2>, <p>, <ul>). Start line 1 with 'Title: <Title>'. Data: {search_data}"
        res = model.generate_content(prompt).text
        title = (
            res.split("\n", 1)[0].replace("Title: ", "").strip()
            if "Title: " in res
            else topic
        )
        body = res.split("\n", 1)[1].strip() if "Title: " in res else res
        wp_status = post_to_wordpress(title, body)
        return f"📝 **Blog Status:** {wp_status}"

    elif user_text.lower().startswith("/lead "):
        target = user_text[6:].strip()
        search_data = search_tavily(f"top business contacts {target}")
        prompt = f"Extract business leads for '{target}' from: {search_data}. Provide Name, Address, and Outreach message."
        return f"🎯 **B2B LEADS:**\n" + model.generate_content(prompt).text

    else:
        return model.generate_content(
            f"Respond directly: {user_text}"
        ).text


def send_telegram_message(chat_id, text):
    if not TELEGRAM_BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    requests.post(url, json=payload)


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)
        try:
            update = json.loads(post_data.decode("utf-8"))
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                user_text = update["message"]["text"]
                reply = generate_ai_response(user_text)
                send_telegram_message(chat_id, reply)
        except Exception as e:
            print(f"Error: {e}")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"status": "ok"}).encode("utf-8"))

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write("<h1>Level 6 Engine Backend is Live!</h1>".encode("utf-8"))