import requests

def telegram_notify(bot_token: str, chat_id: str, message: str):
    if not bot_token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"})
    return resp.ok
